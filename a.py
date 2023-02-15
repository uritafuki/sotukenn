"""
データベースからPDF形式でレポートを生成し、メールに添付して送信する
"""
__author__  = "MindWood"
__version__ = "1.00"
__date__    = "31 Oct 2019"

import MySQLdb
# from reportlab.pdfgen import canvas
# from reportlab.pdfbase import pdfmetrics
# from reportlab.pdfbase.cidfonts import UnicodeCIDFont
# from reportlab.lib import colors
# from reportlab.lib.pagesizes import A4, portrait
# from reportlab.lib.units import mm
# from reportlab.platypus import Table, TableStyle
import smtplib
from email import encoders
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
import os
import datetime

def setup_page():
    """フォントを登録し、ヘッダとフッタを設定する"""
    pdfmetrics.registerFont(UnicodeCIDFont(font_name))  # フォントの登録
    # ヘッダ描画
    c.setFont(font_name, 18)
    c.drawString(10*mm, height - 15*mm, "通信機器稼働状況レポート")
    c.setFont(font_name, 9)
    c.drawString(width - 58*mm, height - 10*mm, header_date)
    # フッタ描画
    c.drawString(10*mm, 16*mm, "直近8時間以内にデータ受信できている端末IDを緑色で表示しています。")
    global page_count
    c.drawString(width - 15*mm, 5*mm, "{}頁".format(page_count))  # ページ番号を描画
    page_count += 1

def control_break():
    """顧客名でコントロールブレイクする"""
    if ctrl_break_key == "": return
    c.showPage()
    setup_page()

def page_break(n):
    """改ページ処理"""
    n += 1
    if n < 28: return n
    c.showPage()
    setup_page()
    return 0

# 基準日時の設定
dt = datetime.datetime.now()
header_date = "{:%Y年%-m月%-d日 %-H時%-M分 現在}".format(dt)
safe_date = "{:%Y/%m/%d %H:%M}".format(dt + datetime.timedelta(hours=-8))  # 8時間前

# PDFファイルの初期設定
pdf_filename = "report{:%y%m}.pdf".format(dt)
c = canvas.Canvas(pdf_filename, pagesize=portrait(A4))  # PDFファイル名と用紙サイズ
width, height = A4  # 用紙サイズの取得
c.setAuthor("MindWood")
c.setTitle("IoT gateway Working report")
c.setSubject("")

font_name = "HeiseiKakuGo-W5"  # フォント名
page_count = customer_no = 1
setup_page()
ctrl_break_key = ""

# MySQLに接続
conn = MySQLdb.connect(host="localhost", user="xxxxxx", passwd="yyyyyy", db="zzzzzz", charset="utf8")
cursor = conn.cursor(MySQLdb.cursors.DictCursor)

# 通信機器のマスタ情報取得
cursor.execute('''
SELECT c.Name as CustName, d.Name as DeptName, a.Code, a.Area, hex(a.MacAddress) as MacAddress
FROM table0001 a
LEFT JOIN table0002 c ON a.CustomerID = c.CustomerID
LEFT JOIN table0003 d ON a.CustomerID = d.CustomerID AND a.DeptID = d.DeptID
ORDER BY c.CustomerID, d.DeptID, MacAddress;
''')

gws = cursor.fetchall()
for row_gw in gws:
    # 顧客名が変わったら改ページ
    if ctrl_break_key != row_gw["CustName"]:
        control_break()
        ctrl_break_key = row_gw["CustName"]
        c.setFont(font_name, 15)
        c.drawString(10*mm, height - 36*mm, "{}. {}".format(customer_no, ctrl_break_key))
        customer_no += 1

        data = [ [ "部署名", "管理コード", "設置エリア", "MACアドレス" ] ]  # 通信機器の見出し
        table = Table(data, colWidths=(70*mm, 40*mm, 40*mm, 40*mm), rowHeights=8*mm)  # 表の作成
        table.setStyle(TableStyle([
            ("FONT", (0, 0), (-1, -1), font_name, 11),            # フォント
            ("BOX", (0, 0), (-1, -1), 1, colors.black),           # 外側罫線
            ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.black),  # 内側罫線
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),               # 文字を縦方向中央に揃える
            ("BACKGROUND", (0, 0), (-1, -1), colors.lightgrey),   # 灰色で塗り潰す
        ]))
        table.wrapOn(c, 10*mm, height - 50*mm)  # 表の位置
        table.drawOn(c, 10*mm, height - 50*mm)  # 表の位置
        line_count = 1

    styles = [
        ("FONT", (0, 0), (-1, -1), font_name, 11),
        ("BOX", (0, 0), (-1, -1), 1, colors.black),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]
    MacAddress = row_gw["MacAddress"]
    if os.uname()[1] == "ip-172-35-10-XX":  # 特定のサーバなら
        MacAddress = "XXXXXXXXXXXX"
        styles.append(("BACKGROUND", (3, 0), (3, 0), colors.yellow))  # 黄色で塗り潰す

    data = [ [ row_gw["DeptName"], row_gw["Code"], row_gw["Area"], MacAddress ] ]  # 通信機器の明細データ
    table = Table(data, colWidths=(70*mm, 40*mm, 40*mm, 40*mm), rowHeights=8*mm)
    table.setStyle(TableStyle(styles))
    table.wrapOn(c, 10*mm, height - 50*mm - 8*mm * line_count)
    table.drawOn(c, 10*mm, height - 50*mm - 8*mm * line_count)
    line_count = page_break(line_count)

    # データ受信日時の取得
    cursor.execute('''
    SELECT hex(TermID) as TermID, from_unixtime(min(Time),"%Y/%m/%d %H:%i:%S") as from_date, from_unixtime(max(Time),"%Y/%m/%d %H:%i:%S") as to_date FROM table0005
    WHERE MacAddress=0x{} GROUP BY TermID ORDER BY to_date;
    '''.format(MacAddress))

    terms = cursor.fetchall()
    for row_term in terms:
        data = [ [ "期間", row_term["from_date"] + " ～ " + row_term["to_date"], "端末ID", row_term["TermID"] ] ]  # 端末の明細データ
        table = Table(data, colWidths=(25*mm, 100*mm, 25*mm, 40*mm), rowHeights=8*mm)
        styles = [
            ("FONT", (0, 0), (-1, -1), font_name, 11),
            ("BOX", (0, 0), (-1, -1), 1, colors.black),
            ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.black),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BACKGROUND", (0, 0), (0, 0), colors.lightgrey),
            ("BACKGROUND", (2, 0), (2, 0), colors.lightgrey),
        ]
        if row_term["to_date"] > safe_date:  # 最終受信日時が直近8時間以内なら
            styles.append(("BACKGROUND", (3, 0), (3, 0), colors.palegreen))
        table.setStyle(TableStyle(styles))
        table.wrapOn(c, 10*mm, height - 50*mm - 8*mm*line_count)
        table.drawOn(c, 10*mm, height - 50*mm - 8*mm*line_count)
        line_count = page_break(line_count)

# MySQLの切断
cursor.close()
conn.close()

# PDFファイルに保存
c.showPage()
c.save()

# PDFファイルをメール送信
from_addr = "xxxxxx@yyyyyy.com"
to_addr   = "zzzzzz@xxxx.co.jp"
bcc_addr  = "xxxxxx@gmail.com"  # カンマ区切りで複数指定可
rcpt = bcc_addr.split(",") + [to_addr]

msg = MIMEMultipart()
msg["Subject"] = "通信機器稼働状況レポート {:%Y年%-m月}".format(dt)
msg["From"] = from_addr
msg["To"] = to_addr

msg.attach(MIMEText("""
本メールはシステムから自動送信しています。
XXXXサーバのシステム稼働状況を添付いたします。
""".strip()))

attachment = MIMEBase("application", "pdf")
file = open(pdf_filename, "rb+")
attachment.set_payload(file.read())
file.close()
encoders.encode_base64(attachment)
attachment.add_header("Content-Disposition", "attachment", filename=pdf_filename)
msg.attach(attachment)

smtp = smtplib.SMTP("smtp.xxxxxx.com", 587)  # SMTPサーバ
smtp.starttls()
smtp.login(from_addr, "PASSWORD")  # パスワード
smtp.sendmail(from_addr, rcpt, msg.as_string())
smtp.close()