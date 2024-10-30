from pathlib import Path

from django.conf import settings
from PIL import Image
# from PIL import ImageDraw
# from PIL import ImageFont

from documents.parsers import DocumentParser

import olefile
# import zlib
# import struct
import io

import os
import pdfkit
import re

from bs4 import BeautifulSoup
import base64


def extract_text_from_html(html_file):
    with open(html_file, 'r', encoding='utf-8') as file:
        html_content = file.read()
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    text = soup.get_text(separator='\n', strip=True)
    
    return text

# Thanks for gpt
def including_image_to_html(xhtml_file, output_file):
    with open(xhtml_file, 'r', encoding='utf-8') as file:
        soup = BeautifulSoup(file, 'html.parser')

    for img in soup.find_all('img'):
        img_src = img['src']
        
        img_path = os.path.join(os.path.dirname(xhtml_file), img_src)
        
        if os.path.isfile(img_path):
            with open(img_path, 'rb') as img_file:
                
                encoded_string = base64.b64encode(img_file.read()).decode('utf-8')
                
                mime_type = 'image/jpeg' if img_src.endswith('.jpg') or img_src.endswith('.jpeg') else 'image/png'
                data_url = f"data:{mime_type};base64,{encoded_string}"
                img['src'] = data_url

    with open(output_file, 'w', encoding='utf-8') as file:
        file.write(str(soup.prettify()))

def including_styles_to_html(html_file_path, style_file_path):
    str_html_file_path = str(html_file_path)
    str_style_file_path = str(style_file_path)

    with open(str_style_file_path, 'r', encoding='utf-8') as css_file:
        css_content = css_file.read()

    new_html_content = []
    with open(str_html_file_path, 'r', encoding='utf-8') as html_file:
        head_inserted = False
        for line in html_file:
            new_html_content.append(line)
            if '<head' in line and not head_inserted:
                new_html_content.append(f'<style>\n{css_content}\n</style>\n')
                head_inserted = True  

    with open(str_html_file_path, 'w', encoding='utf-8') as html_output_file:
        html_output_file.writelines(new_html_content)


def escape_special_chars(filename):
    if filename is None: 
        raise ValueError("filename cannot be None")
    
    if not isinstance(filename, str):
        raise TypeError("filename must be a string")

    special_chars = r' "\'$\\&;|()*?[]{}`' 

    escaped_filename = re.sub(r'([{}])'.format(re.escape(special_chars)), r'\\\1', filename)
    
    return escaped_filename

def hwp_to_html(hwp_file_path: Path, output_html_path):

    escaped_path = escape_special_chars(str(hwp_file_path))

    os.system(f"hwp5html --output {output_html_path} {escaped_path}")
    # TODO; 예외 처리 추가˜

    including_image_to_html(os.path.join(output_html_path, "index.xhtml"), os.path.join(output_html_path, "index.html"))
    including_styles_to_html(os.path.join(output_html_path, "index.html"), os.path.join(output_html_path, "styles.css"))


def html_to_pdf(html_file_path, output_pdf_path):
    str_html_file_path = str(html_file_path)

    try:
        with open(str_html_file_path, 'r', encoding='utf-8') as file:
            html_content = file.read()  # 
            # print(html_content)         
    except FileNotFoundError:
        print(f"Error: File '{str_html_file_path}' not found.")
    except Exception as e:
        print(f"An error occurred: {e}")
    try:
        pdfkit.from_file(str(html_file_path), str(output_pdf_path), options={"enable-local-file-access": ""})
        print(f"Converted {html_file_path} to {output_pdf_path}")
    except Exception as e:
        print(f"Error during HTML to PDF conversion: {e}")
        return False
    return True


# 줄바꿈 등이 한자로 들어가는 이슈로 hwp5html을 통해서 추출하는것으로 대체
# def get_hwp_text(filename):
#     f = olefile.OleFileIO(filename)
#     dirs = f.listdir()

#     if ["FileHeader"] not in dirs or \
#             ["\x05HwpSummaryInformation"] not in dirs:
#         raise Exception("Not Valid HWP.")

#     header = f.openstream("FileHeader")
#     header_data = header.read()
#     is_compressed = (header_data[36] & 1) == 1

#     nums = []
#     for d in dirs:
#         if d[0] == "BodyText":
#             nums.append(int(d[1][len("Section"):]))
#     sections = ["BodyText/Section" + str(x) for x in sorted(nums)]

#     text = ""
#     for section in sections:
#         bodytext = f.openstream(section)
#         data = bodytext.read()
#         if is_compressed:
#             unpacked_data = zlib.decompress(data, -15)
#         else:
#             unpacked_data = data

#         section_text = ""
#         i = 0
#         size = len(unpacked_data)
#         while i < size:
#             header = struct.unpack_from("<I", unpacked_data, i)[0]
#             rec_type = header & 0x3ff
#             rec_len = (header >> 20) & 0xfff

#             if rec_type in [67]:
#                 rec_data = unpacked_data[i + 4:i + 4 + rec_len]
#                 section_text += rec_data.decode('utf-16')
#                 section_text += "\n"

#             i += 4 + rec_len

#         text += section_text
#         text += "\n"

#     return text


class HwpDocumentParser(DocumentParser):
    logging_name = "paperless.parsing.text"

    def get_thumbnail(self, document_path: Path, mime_type, file_name=None) -> Path:
        ole = olefile.OleFileIO(document_path)

        if ole.exists('PrvImage'):
            # hwp 내의 썸네일 이미지 사용
            thumbnail_data = ole.openstream('PrvImage').read()

            image = Image.open(io.BytesIO(thumbnail_data))
            
            upscale_factor = 2 
            new_size = (image.width * upscale_factor, image.height * upscale_factor)
            image = image.resize(new_size, Image.LANCZOS)

            out_path = self.tempdir / "thumb.webp"
            image.save(out_path, format="WEBP")
        else:
            print("Can't get thumbnail")

        ole.close()

        return out_path

    def parse(self, document_path, mime_type, file_name=None):
        pdf_out_path = self.tempdir / "archived.pdf"
        html_out_path = os.path.join(self.tempdir, "html")
        
        # hwp를 html 변경
        hwp_to_html(document_path, html_out_path)

        # html을 pdf로 변환
        html_to_pdf(os.path.join(html_out_path, 'index.html'), pdf_out_path)

        self.archive_path = pdf_out_path

        # self.text = get_hwp_text(document_path)
        self.text = extract_text_from_html(os.path.join(html_out_path, "index.html"))

    def get_settings(self):
        return None

