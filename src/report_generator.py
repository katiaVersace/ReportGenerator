'''
Created on 07 giu 2019

@author: katia

'''


import time
from io import BytesIO
from math import ceil
from matplotlib import pyplot as plt
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT, TA_JUSTIFY
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Flowable
from reportlab.lib.units import inch, mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from pdfrw import PdfReader, PdfDict
from pdfrw.buildxobj import pagexobj
from pdfrw.toreportlab import makerl
from pdfrw import PdfReader, PdfDict
from pdfrw.buildxobj import pagexobj
from pdfrw.toreportlab import makerl
from reportlab.platypus import  Image
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.units import cm
import pandas as pandas
import matplotlib
from datetime import datetime
import matplotlib.dates as mdates
from pandas.plotting import _converter
import subprocess
from tkinter import Tk, Label, Button, Entry, StringVar, END
from tkinter.filedialog import askopenfilename
import os.path
from tkinter import messagebox


def form_xo_reader(imgdata):
    page, = PdfReader(imgdata).pages
    return pagexobj(page)

def first_page_simple(canvas, doc):
    laters_page(canvas, doc)
    canvas.setLineWidth(2)
    canvas.line(30,718,560,718)
        
def first_page_detailed(canvas, doc):
    laters_page(canvas, doc)
    canvas.setLineWidth(2)
    canvas.line(30,790,560,790)

def laters_page(canvas, doc):
    """
    Add the page number and logo
    """
    page_num = canvas.getPageNumber()
    canvas.setFont("Helvetica", 10)
    canvas.drawRightString(190*mm, 10*mm, " Página %s" %page_num)
    wada_logo="wada_logo.png"
    
    canvas.drawImage(wada_logo, 20 * mm, 5 * mm)

    
class PlotData:
    """
    This class is simply a container. It is composed from xAxis and yAxis that will be plotted
    """
    def __init__(self, xAxis, yAxis):
        self.xAxis=xAxis
        self.yAxis=yAxis
          
class PdfImage(Flowable):
    def __init__(self, img_data, width=200, height=200, hAlign=None):
        super().__init__()
        self.img_width = width
        self.img_height = height
        self.img_data = img_data


        if hAlign:
            # Only set hAlign if passed, otherwise use what's default from
            # Flowable's constructor
            self.hAlign=hAlign

    def wrap(self, width, height):
        return self.img_width, self.img_height

    def drawOn(self, canv, x, y, _sW=0):
        if _sW > 0 and hasattr(self, 'hAlign'):
            a = self.hAlign
            if a in ('CENTER', 'CENTRE', TA_CENTER):
                x += 0.5*_sW
            elif a in ('RIGHT', TA_RIGHT):
                x += _sW
            elif a not in ('LEFT', TA_LEFT):
                raise ValueError("Bad hAlign value " + str(a))
        canv.saveState()
        img = self.img_data
        if isinstance(img, PdfDict):
            xscale = self.img_width / img.BBox[2]
            yscale = self.img_height / img.BBox[3]
            canv.translate(x, y)
            canv.scale(xscale, yscale)
            canv.doForm(makerl(canv, img))
        else:

            canv.drawImage(img, x, y, self.img_width, self.img_height)
            # preserveAspectRatio=True, mask='auto', anchor='c')
        canv.restoreState()


    
def readCsv(path, avg_data, min_data, search_factor_data, detailed, ramais, km_de_conduta, pesquisa_ramais_data, pesquisa_km_data):
    """
    This method open the csv file and take the first date. For each row in the csv file, until the date is the same
    it sums the flow and calculate the minimum flow. When the date is new or the file ends, it calculate the average flow for that date.
    All this data for each date are kept in 5 PlotData each for every line in the plots.
    """
    

    
    
    data = pandas.read_csv(path, delimiter=';', decimal=',',skiprows=2)

    x_avg_data=[]
    y_avg_data=[]
    
    x_min_data=[]
    y_min_data=[]
    
    x_search_factor_data=[]
    y_search_factor_data=[]
    
    if ramais!=0 and km_de_conduta!=0:
        x_pesquisa_ramais_data=[]   
        y_pesquisa_ramais_data=[]
    
        x_pesquisa_km_data=[]
        y_pesquisa_km_data=[]
       
    lastDate=0

    for index, row in data.iterrows():
       
        date = row['Data']
        read_value = row['Leitura']
        flow = row['Caudal']
        
        currentDate=datetime.strptime(date, '%d/%m/%Y %H:%M').date()
        #new date read or end of file
        if currentDate!=lastDate or index==data.iloc[-1].name :
            #if this is not the first row of the document and date is changed execute the calculations
            if lastDate!=0:
                
                avg_flow=round(tot_flow_current_day/days,2)
                y_avg_data.insert(0,avg_flow)
                x_avg_data.insert(0,lastDate)
                
                
                x_min_data.insert(0,min_time)
                y_min_data.insert(0,min_flow)
                
                current_day_search_factor=round(min_flow/avg_flow,2)
                x_search_factor_data.insert(0,lastDate)
                y_search_factor_data.insert(0,current_day_search_factor)
                
                if detailed:
                    x_pesquisa_ramais_data.insert(0,lastDate)   
                    y_pesquisa_ramais_data.insert(0,round(min_flow/ramais,3))
    
                    x_pesquisa_km_data.insert(0,lastDate)  
                    y_pesquisa_km_data.insert(0,round(min_flow/km_de_conduta,3))
        
                
                
            lastDate=currentDate
            tot_flow_current_day=flow
            
            min_flow=flow
            min_time=lastDate
            
            days=1
        
        #processing data of the same date     
        else: 
            
            tot_flow_current_day+=float(flow)
            days+=1
           
            if flow<min_flow:
                min_flow=flow
                min_time=lastDate
    
    avg_data=PlotData(x_avg_data,y_avg_data)
    min_data=PlotData(x_min_data,y_min_data)
    search_factor_data=PlotData(x_search_factor_data,y_search_factor_data)
    
    if detailed:
        pesquisa_ramais_data=PlotData(x_pesquisa_ramais_data,y_pesquisa_ramais_data)
        pesquisa_km_data=PlotData(x_pesquisa_km_data,y_pesquisa_km_data)
    
    return avg_data, min_data, search_factor_data, pesquisa_ramais_data, pesquisa_km_data
    
    
def make_plot1(use_pdfrw, avg_data, min_data, plt, detailed):
    """
    This method plots the data about the average flow (blue) and the minimum flow (green). This is the first plot of the document
    """
    width_img=19
    height_img=6
    if detailed:
        height_img=4

    fig = plt.figure(figsize=(width_img,height_img))
    plt.plot( avg_data.xAxis,avg_data.yAxis, color='#335469', linewidth=6)
    plt.plot( min_data.xAxis,min_data.yAxis, color='#B9D484', linewidth=6)
    plt.tight_layout() 
    plt.xlabel('DIA')
    plt.ylabel('CAUDAL (m3/h)')
    ax = plt.gca()
    #set visible only the bottom line
    ax.spines['bottom'].set_color('#B9D484')
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['top'].set_visible(False)
    #setup the labels
    ax.set_xticks(avg_data.xAxis)
    ax.set_xticklabels(avg_data.xAxis)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%b'))
    plt.xticks(rotation=45)
    ax.grid(which='major', axis='x', linestyle='--')
    ax.legend(('Caudal Mínimo Noturno','Caudal médio diário'))
    #Calculate the max of green line and the corresponding point on the blue line
    ymax_green = max(min_data.yAxis)
    xpos = min_data.yAxis.index(ymax_green)
    xmax = min_data.xAxis[xpos]
    ymax_blue=avg_data.yAxis[xpos]
    ax.annotate(
        str(ymax_green),
        xy=(xmax, ymax_green), xytext=(28, 10),
        textcoords='offset points', ha='right', va='bottom')
    ax.annotate(
        str(ymax_blue),
        xy=(xmax, ymax_blue), xytext=(28, 10),
        textcoords='offset points', ha='right', va='bottom')
    #get image
    imgdata = BytesIO()
    fig.savefig(imgdata, format='pdf' if use_pdfrw else 'png',bbox_inches='tight')
    imgdata.seek(0)
    reader = form_xo_reader if use_pdfrw else ImageReader
    image = reader(imgdata)
    test_scale = 100 * 0.25
    img = PdfImage(image, width=ceil(width_img*test_scale), height=ceil(height_img*test_scale), hAlign=TA_CENTER)
    return img
    

def make_plot2(use_pdfrw, search_factor_data, plt, detailed):
    """
    This method plots the data about the Search Factor. This is the second plot of the document. If the document is detailed
    this plot will be smaller
    """

    
    width_img=19
    height_img=6
    if detailed:
        width_img=12
        height_img=4
    fig = plt.figure(figsize=(width_img,height_img))
    plt.plot( search_factor_data.xAxis,search_factor_data.yAxis, color='#B9D484', linewidth=6, label='Fator de Pesquisa')
    plt.xlabel('DIA')
    plt.ylabel('FATOR DE PESQUISA')
    ax = plt.gca()
    ax.set_ylim([0,1])
    #set visible only the bottom line
    ax.spines['bottom'].set_color('#B9D484')
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['top'].set_visible(False)
    #calculate the max
    ymax_green = max(search_factor_data.yAxis)
    xpos = search_factor_data.yAxis.index(ymax_green)
    xmax = search_factor_data.xAxis[xpos]
    ax.annotate(
        str(ymax_green),
        xy=(xmax, ymax_green), xytext=(28, 10),
        textcoords='offset points', ha='right', va='bottom')
    #setup the labels
    ax.set_xticks(search_factor_data.xAxis)
    ax.set_xticklabels(search_factor_data.xAxis)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%b'))
    plt.xticks(rotation=45)
    ax.grid(which='major', axis='x', linestyle='--')
    ax.legend(bbox_to_anchor=(0.5, 1.0))
    #get image
    imgdata = BytesIO()
    fig.savefig(imgdata, format='pdf' if use_pdfrw else 'png', bbox_inches='tight')
    imgdata.seek(0)
    reader = form_xo_reader if use_pdfrw else ImageReader
    image = reader(imgdata)
    test_scale = 100 * 0.25
    img = PdfImage(image, width=ceil(width_img*test_scale), height=ceil(height_img*test_scale), hAlign=TA_CENTER)
    return img


def make_plot3(use_pdfrw, pesquisa_ramais_data, plt):
    """
    This method plots the data about the Potencial de pesquisa por número de ramais. This is the third plot of the document.
    """
     
    fig = plt.figure(figsize=(13,4))
    plt.plot( pesquisa_ramais_data.xAxis,pesquisa_ramais_data.yAxis, color='#335469', linewidth=6, label='Potencial de pesquisa')
    plt.xlabel('DIA')
    plt.ylabel('POTENCIAL DE PESQUISA (m3/h/ramais)')
    ax = plt.gca()
    ax.set_ylim([0,1])
    #Show only the bottom line
    ax.spines['bottom'].set_color('#335469')
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['top'].set_visible(False)
    #calculate the max
    ymax = max(pesquisa_ramais_data.yAxis)
    xpos = pesquisa_ramais_data.yAxis.index(ymax)
    xmax = pesquisa_ramais_data.xAxis[xpos]
    ax.annotate(
        str(ymax),
        xy=(xmax, ymax), xytext=(28, 10),
        textcoords='offset points', ha='right', va='bottom')
    #setup labels
    ax.set_xticks(pesquisa_ramais_data.xAxis)
    ax.set_xticklabels(pesquisa_ramais_data.xAxis)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%b'))
    plt.xticks(rotation=45)
    ax.grid(which='major', axis='x', linestyle='--')
    ax.legend(bbox_to_anchor=(0.5, 1.0))
    #get image
    imgdata = BytesIO()
    fig.savefig(imgdata, format='pdf' if use_pdfrw else 'png',bbox_inches='tight')
    imgdata.seek(0)
    reader = form_xo_reader if use_pdfrw else ImageReader
    image = reader(imgdata)
    test_scale = 100 * 0.25
    img = PdfImage(image, width=ceil(13*test_scale), height=ceil(4*test_scale), hAlign=TA_CENTER)
    return img

def make_plot4(use_pdfrw, pesquisa_km_data, plt):
    """
    This method plots the data about the Potencial de pesquisa por km de conduta. This is the fourth and last plot of the document.
    """
 
    fig = plt.figure(figsize=(13,4))
    plt.plot( pesquisa_km_data.xAxis,pesquisa_km_data.yAxis, color='#B9D484', linewidth=6, label='Potencial de pesquisa')
    plt.xlabel('DIA')
    plt.ylabel('POTENCIAL DE PESQUISA (m3/h/km)')
    ax = plt.gca()
    ax.set_ylim([0,1])
    #Show only the bottom line
    ax.spines['bottom'].set_color('#B9D484')
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['top'].set_visible(False)
    #calculate the max
    ymax = max(pesquisa_km_data.yAxis)
    xpos = pesquisa_km_data.yAxis.index(ymax)
    xmax = pesquisa_km_data.xAxis[xpos]    
    ax.annotate(
        str(ymax),
        xy=(xmax, ymax), xytext=(28, 10),
        textcoords='offset points', ha='right', va='bottom')
    #setup labels
    ax.set_xticks(pesquisa_km_data.xAxis)
    ax.set_xticklabels(pesquisa_km_data.xAxis)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%b'))
    plt.xticks(rotation=45)
    ax.grid(which='major', axis='x', linestyle='--')
    ax.legend(bbox_to_anchor=(0.5, 1.0))
    #get image
    imgdata = BytesIO()
    fig.savefig(imgdata, format='pdf' if use_pdfrw else 'png',bbox_inches='tight')
    imgdata.seek(0)
    reader = form_xo_reader if use_pdfrw else ImageReader
    image = reader(imgdata)
    test_scale = 100 * 0.25
    img = PdfImage(image, width=ceil(13*test_scale), height=ceil(4*test_scale), hAlign=TA_CENTER)
    return img

def make_simple_report(outfn,use_pdfrw, entidade, local,canal, avg_data, min_data, search_factor_data):
    """
    This method builds a simple report. 
    """  

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY))
    style_right = ParagraphStyle(name='right', parent=styles['Normal'], alignment=TA_RIGHT)
    style_center = ParagraphStyle(name='center', parent=styles['Normal'], alignment=TA_CENTER)
    doc = SimpleDocTemplate(outfn)
   
    story = []

    story.append(Paragraph("<b>RELATÓRIO SÍNTESE SEMANAL</b>", styles["Title"]))
    
    time.ctime()
    timestamp = '<font size=12>%s</font>' % time.strftime("X%d de %b de %Y").replace('X0','X').replace('X','')
    story.append(Paragraph(timestamp,style_center))
    story.append(Spacer(1, 0.5 * inch))
    
    story.append(Paragraph("<b>Entidade:</b> "+entidade, styles["Normal"]))
    story.append(Paragraph("<b>Local:</b> "+local, styles["Normal"]))
    story.append(Paragraph("<b>Canal:</b> "+canal, styles["Normal"]))
    story.append(Spacer(1, 0.2 * inch))
    
    story.append(Paragraph('<b>Evolução dos caudais mínimos noturno e médios diários </b>', styles["Normal"]))
    story.append(Spacer(1, 0.2 * inch))
     
    plot1= make_plot1(use_pdfrw, avg_data, min_data, plt, False)
    story.append(plot1)
    story.append(Spacer(1, 0.2 * inch))
    
    story.append(Paragraph('<b>Fator de Pesquisa</b>', styles["Normal"]))
    story.append(Spacer(1, 0.2 * inch))
    
    plot2=make_plot2(use_pdfrw,  search_factor_data, plt, False)
    story.append(plot2)
    story.append(Spacer(1, 0.2 * inch))
    
    story.append(Paragraph('<b>Valores de Referência</b>', styles["Normal"]))
    story.append(Spacer(1, 0.2 * inch))
    
    #table with reference values
    reference_values_data = []
    column1Heading = Paragraph('<b>Fator de pesquisa (Fp)</b>', style_center)
    column2Heading = Paragraph('<b>Estado</b>', style_center)
    column3Heading = Paragraph('<b>Cor</b>', style_center)
        
    reference_values_data.append([column1Heading,column2Heading,column3Heading])
    green="green.png"
    yellow="yellow.png"
    red="red.png"
    
    green_img = Image(green, 0.2*inch, 0.2*inch)
    yellow_img = Image(yellow, 0.2*inch, 0.2*inch)
    red_img = Image(red, 0.2*inch, 0.2*inch)
    
    reference_values_data.append(["Fp <= 0.3","Bom",green_img])
    reference_values_data.append(["0.3 < Fp <= 0.5","Razoável",yellow_img])
    reference_values_data.append(["Fp > 0.5","Preocupante",red_img])

    reference_values = Table(reference_values_data, [4.5 * cm, 3 * cm,2 * cm], repeatRows=1)
    reference_values.hAlign = 'LEFT'
    tblStyle = TableStyle([
                       ('LINEAFTER', (0,0), (-2,0), 0.25, colors.black),
                       ('LINEAFTER', (0,1), (-2,1), 0.25, colors.black),
                       ('LINEAFTER', (0,2), (-2,2), 0.25, colors.black),
                       ('LINEAFTER', (0,3), (-2,3), 0.25, colors.black),
                       ('ALIGN', (0, 0), (-1, -1), "CENTER"),
                     
                       ])

    reference_values.setStyle(tblStyle)

    story.append(reference_values)
    story.append(Spacer(1, 0.4 * inch))

    #table with Observation
    observation_title= Paragraph('<b>Observações</b>', styles["Normal"])
    observation_content=Paragraph(make_observation(),ParagraphStyle("autoBreak", wordWrap = 'CJK'))
    datas= [[observation_title, observation_content]]
    table2=Table(datas, [2.7 * cm, 14 * cm], hAlign='LEFT')
    table2.setStyle(TableStyle([    
                       ('BOX', (0,0), (0,0), 0.25, colors.green),
                       ('ALIGN', (0, 0), (0,0), "CENTER"),
                       ('VALIGN', (0,0), (0,0), 'MIDDLE'),]))
    story.append(table2)

    doc.build(story, onFirstPage=first_page_simple, onLaterPages=laters_page)
    

    
    

def make_detailed_report(outfn,use_pdfrw, entidade, local,canal, avg_data, min_data, search_factor_data,pesquisa_ramais_data, pesquisa_km_data, ramais, km_de_conduta):
    """
    This method builds a detailed report.
    """
   
    
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY))
    style_right = ParagraphStyle(name='right', parent=styles['Normal'], alignment=TA_RIGHT)
    style_center = ParagraphStyle(name='center', parent=styles['Normal'], alignment=TA_CENTER)
    style_center_with_size8 = ParagraphStyle(name='center_size', parent=styles['Normal'], alignment=TA_CENTER, fontSize=8)
    style_center_with_size13 = ParagraphStyle(name='center_size', parent=styles['Normal'], alignment=TA_CENTER, fontSize=13)
    style_bordered=ParagraphStyle(name='bordered', parent=styles['Normal'], alignment=TA_RIGHT,borderWidth= 1,leftIndent=100,paddingRight=20,
                                  borderColor= '#B9D484',
                                  borderRadius=1
                                  )
    
    doc = SimpleDocTemplate(outfn,  topMargin=10)
   
    story = []

    story.append(Paragraph("<b>RELATÓRIO SÍNTESE SEMANAL</b>", style_center_with_size13))
    story.append(Spacer(1, 0.1 * inch))    
    
    time.ctime()
    timestamp = '<font size=12>%s</font>' % time.strftime("X%d de %b de %Y").replace('X0','X').replace('X','')
    story.append(Paragraph(timestamp,style_center_with_size8))
    story.append(Spacer(1, 0.2 * inch))
    
    story.append(Paragraph("<b>Entidade:</b> "+entidade, styles["Normal"]))
    story.append(Paragraph("<b>Local:</b> "+local, styles["Normal"]))
    story.append(Paragraph("<b>Canal:</b> "+canal, styles["Normal"]))
    story.append(Spacer(1, 0.2 * inch))
    
    story.append(Paragraph('<b>Evolução dos caudais mínimos noturno e médios diários </b>', styles["Normal"]))
    story.append(Spacer(1, 0.2 * inch))
      
    plot1= make_plot1(use_pdfrw, avg_data, min_data, plt, True)
    plot1.hAlign="LEFT"
    story.append(plot1)
    story.append(Spacer(1, 0.2 * inch))
    
    #table1 contains on left the Search Factor plot and on right the table with reference values
    table1_data=[]
    table1_data.append([Paragraph('<b>Fator de Pesquisa</b>', styles["Normal"]),Paragraph('<b>Valores de Referência</b>',style_right)])
    
    reference_values_data = []
    column1Heading = Paragraph('<b>Fator de pesquisa (Fp)</b>', style_center_with_size8)
    column2Heading = Paragraph('<b>Estado</b>', style_center_with_size8)
    column3Heading = Paragraph('<b>Cor</b>', style_center_with_size8)
    
    reference_values_data.append([column1Heading,column2Heading,column3Heading])
    green="green.png"
    yellow="yellow.png"
    red="red.png"
    
    green_img = Image(green, 0.15*inch, 0.15*inch)
    yellow_img = Image(yellow, 0.15*inch, 0.15*inch)
    red_img = Image(red, 0.15*inch, 0.15*inch)
    
    reference_values_data.append(["Fp <= 0.3","Bom",green_img])
    reference_values_data.append(["0.3 < Fp <= 0.5","Razoável",yellow_img])
    reference_values_data.append(["Fp > 0.5","Preocupante",red_img])

    reference_values_table = Table(reference_values_data, [3.5 * cm, 2 * cm,1 * cm], repeatRows=1)
    reference_values_table.hAlign = 'LEFT'
    tblStyle = TableStyle([
                       ('LINEAFTER', (0,0), (-2,0), 0.25, colors.black),
                       ('LINEAFTER', (0,1), (-2,1), 0.25, colors.black),
                       ('LINEAFTER', (0,2), (-2,2), 0.25, colors.black),
                       ('LINEAFTER', (0,3), (-2,3), 0.25, colors.black),
                       ('ALIGN', (0, 0), (-1, -1), "CENTER"),
                       ('FONTSIZE',(0, 0), (-1, -1), 8)  ])

    reference_values_table.setStyle(tblStyle)
    
    style1 = TableStyle([ ('VALIGN', (1, 0), (-1, -1), "CENTER")                                  
                       ])
    
    plot2=make_plot2(use_pdfrw, search_factor_data, plt, True)
    table1_data.append([plot2,reference_values_table])
    
    table1=Table(table1_data,[11*cm,5*cm])
    table1.setStyle(style1)
    story.append(table1)
    story.append(Spacer(1, 0.2 * inch))
    
    #table2 contains on left the plot about Potencial de pesquisa por número de ramais, on right the number of ramais
    table2_data=[]
    table2_data.append([Paragraph('<b>Potencial de pesquisa por número de ramais </b>', styles["Normal"]),Paragraph('<b> Número de ramais</b>',style_right)])
    plot3=make_plot3(use_pdfrw, pesquisa_ramais_data, plt)
    plot3.hAlign="LEFT"
    
    table2_data.append([plot3,Paragraph(str(ramais), style_bordered)])
    
    table2=Table(table2_data,[11*cm,5*cm])
    
    style2 = TableStyle([('VALIGN', (1, 0), (-1, -1), "TOP")  
                       ])
    table2.setStyle(style2)
    story.append(table2)
    story.append(Spacer(1, 0.2 * inch))
    
    #table3 contains on left the plot about Potencial de pesquisa por km de conduta, on right the number of km de conduta
    table3_data=[]
    table3_data.append([Paragraph('<b>Potencial de pesquisa por km de conduta</b>', styles["Normal"]),Paragraph('<b>Quilómetros de conduta</b>',style_right)])
    plot4=make_plot4(use_pdfrw, pesquisa_km_data, plt)
    plot4.hAlign="LEFT"
    
    table3_data.append([plot4,Paragraph(str(km_de_conduta), style_bordered)])
    
    table3=Table(table3_data,[11*cm,5*cm])
    table3.setStyle(style2)
    story.append(table3)
    story.append(Spacer(1, 0.2 * inch))

    #table 4 contains the data about observation. On left the title and on right the content
    observation_title= Paragraph('<b>Observações</b>', styles["Normal"])
    observation_content=Paragraph(make_observation(),ParagraphStyle("autoBreak", wordWrap = 'CJK'))
    table4_data= [[observation_title, observation_content]]
    table4=Table(table4_data, [2.7 * cm, 14 * cm], hAlign='LEFT')
    table4.setStyle(TableStyle([    
                       ('BOX', (0,0), (0,0), 0.25, colors.green),
                       ('ALIGN', (0, 0), (0,0), "CENTER"),
                       ('VALIGN', (0,0), (0,0), 'MIDDLE'),]))
    story.append(table4)

    doc.build(story, onFirstPage=first_page_detailed, onLaterPages=laters_page)
    


def make_observation():
    return "A evolução histórica do caudal noturno registou um aumento de consumo no reservatório na noite do dia 8 de maio de 2019, tendo o caudal médio diário acompanhado esta tendência."



def showGUI():
    
    _converter.register()
    
    window = Tk()
    window.title("Wada Report Generator")
    window.geometry('350x150')
 
    csvPath_lbl = Label(window, text="File csv", background = '#335469', foreground = "white")
    csvPath_lbl.grid(column=0, row=0)
    csv_default_text = StringVar(window, value='test3.csv')
    csvPath_txt = Entry(window,width=30, textvariable=csv_default_text)
    csvPath_txt.grid(column=1, row=0)
    
    browse_file_btn = Button(window, text="Browse File", command=lambda:OpenFile(csvPath_txt))
    
    browse_file_btn.grid(column=2 ,row=0)
    

    entidade_lbl = Label(window, text="Entidade", background = '#335469', foreground = "white")
    entidade_lbl.grid(column=0, row=1)
    entidade_default_text = StringVar(window, value="Município de Penacova")
    entidade_txt = Entry(window,width=30, textvariable=entidade_default_text)
    entidade_txt.grid(column=1, row=1)


    local_lbl = Label(window, text="Local", background = '#335469', foreground = "white")
    local_lbl.grid(column=0, row=2)
    local_default_text = StringVar(window, value="Reservatório da Aveleira ")
    local_txt = Entry(window,width=30, textvariable=local_default_text)
    local_txt.grid(column=1, row=2)


    canal_lbl = Label(window, text="Canal", background = '#335469', foreground = "white")
    canal_lbl.grid(column=0, row=3)
    canal_default_text = StringVar(window, value="example canal")
    canal_txt = Entry(window,width=30, textvariable=canal_default_text)
    canal_txt.grid(column=1, row=3)


    ramais_lbl = Label(window, text="Ramais", background = '#335469', foreground = "white")
    ramais_lbl.grid(column=0, row=4)
    ramais_default_text = StringVar(window, value='2')
    ramais_txt = Entry(window,width=30, textvariable=ramais_default_text)
    ramais_txt.grid(column=1, row=4)


    km_de_conduta_lbl = Label(window, text="Km de conduta", background = '#335469', foreground = "white")
    km_de_conduta_lbl.grid(column=0, row=5)
    km_de_conduta_default_text = StringVar(window, value='10')
    km_de_conduta_txt = Entry(window,width=30, textvariable=km_de_conduta_default_text)
    km_de_conduta_txt.grid(column=1, row=5)


    btn = Button(window, text="Generate", command=lambda:generate(csvPath_txt.get(),entidade_txt.get(), local_txt.get(),canal_txt.get(), ramais_txt.get(),km_de_conduta_txt.get()))
    btn.grid(column=2, row=5)
    
    window.protocol("WM_DELETE_WINDOW", on_closing)
    window.configure(background='#335469')
    window.mainloop()

def on_closing():
    exit()
    
def OpenFile(csv_path_txt):
    name = askopenfilename(filetypes =(("Text File", "*.csv"),("All Files","*.*")),
                           title = "Choose a file."
                           )
    csv_path_txt.delete(0, END) #deletes the current value
    csv_path_txt.insert(0, name)
    
    

def generate(csvPath,entidade, local, canal, _ramais, _km_de_conduta):
    detailed=False
    avg_data=PlotData([],[])
    min_data=PlotData([],[])
    search_factor_data=PlotData([],[])
    pesquisa_ramais_data=PlotData([],[])
    pesquisa_km_data=PlotData([],[])
        
       
    if _ramais=="" or _km_de_conduta=="":
       ramais=0
       km_de_conduta=0
    else:
       ramais=int(_ramais)
       km_de_conduta=int(_km_de_conduta)
    
    
    if csvPath=="" or entidade=="" or local=="" or canal=="":
         messagebox.showinfo("Error", "Fill in the mandatory fields")
    else:
        if os.path.exists(csvPath):
                    
             if ramais==0 or km_de_conduta==0:
                 avg_data, min_data, search_factor_data, pesquisa_ramais_data, pesquisa_km_data=readCsv(csvPath,  avg_data, min_data, search_factor_data, detailed, ramais, km_de_conduta, pesquisa_ramais_data, pesquisa_km_data)
                 make_simple_report("Relatório_semanal_"+entidade+"_pdf.pdf",True, entidade, local,canal, avg_data, min_data, search_factor_data)
                 make_simple_report("Relatório_semanal_"+entidade+"_png.pdf",False, entidade, local,canal, avg_data, min_data, search_factor_data)
        
             else:
                detailed=True
                avg_data, min_data, search_factor_data, pesquisa_ramais_data, pesquisa_km_data=readCsv(csvPath,  avg_data, min_data, search_factor_data, detailed, ramais, km_de_conduta, pesquisa_ramais_data, pesquisa_km_data)
                make_detailed_report("Relatório_semanal_"+entidade+"_pdf.pdf",True, entidade, local,canal, avg_data, min_data, search_factor_data,pesquisa_ramais_data,pesquisa_km_data, ramais, km_de_conduta)
                make_detailed_report("Relatório_semanal_"+entidade+"_png.pdf",False, entidade, local,canal, avg_data, min_data, search_factor_data, pesquisa_ramais_data, pesquisa_km_data,ramais, km_de_conduta)
        
             subprocess.Popen(["Relatório_semanal_"+entidade+"_pdf.pdf"], shell=True)
        else:
            messagebox.showinfo("Error", "Insert a valid path for the csv file")


if __name__ == "__main__":
   
   
    showGUI()