import re
import sys

from pyPdf import PdfFileWriter, PdfFileReader


class WatermarkAdder(object):

    def __init__(self, watermark_filename):
        self.watermark_filename = watermark_filename

    def __call__(self, filename, watermarked_pdf_filename):
        self.watermark = PdfFileReader(open(self.watermark_filename, 'rb')).getPage(0)
        self.watermarked_pdf_filename = watermarked_pdf_filename

        self.filename = filename
        #self.output_filename = re.sub(r'\.pdf', '_wm.pdf', self.filename)
        self.pdf = PdfFileReader(open(self.filename, 'rb'))
        self.output = PdfFileWriter()

        self.add_watermark()

    def add_watermark(self):
        for pagenum in range(self.pdf.getNumPages()):
            page = self.pdf.getPage(pagenum)
            page = self.add_to_page(page)
            self.output.addPage(page)
        self.save()

    def add_to_page(self, page):
        page.mergePage(self.watermark)
        return page

    def save(self):
        output_stream = open(self.watermarked_pdf_filename, 'wb')
        self.output.write(output_stream)
        output_stream.close
