# -*- coding: utf-8
'''
Created on %(date)
@author:Yujin Wang
This is used to parse the info. of FEM
'''
import os
import sqlite3
import numpy as np,pandas as pd
from funmodule import *
from Post import *


@try_except
def FindFile(start, name):
	#Find the files whose name string contains str(name), and the directory of files
	isFlag = 0
	lenname = len(name)
	if  '*' in name:
		name = name.strip('*')
		isFlag =1
		lenname = len(name)-1
	relpath =[]
	files_set = []
	dirs = []
	dirs_set = []

	if isFlag == 0:
		for relpath, dirs, files in os.walk(start):
			for i in files:
				if name == i[-lenname:]:
					full_path = os.path.join(start, relpath, i)
					files_set.append(os.path.normpath(os.path.abspath(full_path)))
					dirs_set.append(os.path.join(start, relpath))
						
	elif isFlag == 1:
		for relpath, dirs, files in os.walk(start):
			for i in files:
				if os.path.splitext(i)[-1] == name:
					full_path = os.path.join(start, relpath, i)
					files_set.append(os.path.normpath(os.path.abspath(full_path)))
					dirs_set.append(os.path.join(start, relpath))
	
	dirs_set = list(set(dirs_set))
	return files_set,dirs_set

class basic():
	def __init__(self,*vars,**kwargs):
		try:
			self.src = vars[0]
			self.checkresult = vars[1]
			self.files = FindFile(self.src , vars[2])
		except:
			pass

class DynaInfo(basic):
	@try_except
	@exeTime
	def Pars(self,keyfiles):
		'''
		parse the key files
		keyfiles -- dyna files list
		'''
		for keyfile in keyfiles:
			ParsFlag = 0
			print '##################'
			print 'Key file:',keyfile
			print '##################'
			for line in open(keyfile):
				try:#
					data = string_split(line[:-1],' ')
					if '*' in line and line.strip()[0] != '$' :
						if data[0][1:] not in dir(self):
							keyword = 'self.' + data[0][1:]
							cmd = keyword + '=[]'
							exec(cmd)
						else:
							keyword = 'self.' + data[0][1:]
						if  'ELEMENT_'  in line:
							ParsFlag = 1
							delta = 8
							continue
						elif 'MAT_'  in line:
							ParsFlag = 1
							delta = 10
							continue
						else:
							ParsFlag = 0
					elif (line[0] != '$' and '*' not in line and ParsFlag == 0):
							cmd = keyword + '.append(data)'
							exec (cmd)	
					elif (line[0] != '$' and '*' not in line and ParsFlag ==1):
							try:
								data = [int(line[0+delta*i:delta+delta*i]) for i in range(len(line[:-1])/delta)]
							except:
								# print 'WARNNING:',line
								data = [line[0+delta*i:delta+delta*i].strip() for i in range(len(line[:-1])/delta)]
							cmd = keyword + '.append(data)'
							exec (cmd)	
				except:
							print 'ERROR:',line
		return self

	def DynaFormat1(self,listRow):
		'''
		Dyna format:%10s per word
		data -- list
		'''
		string = ''
		for data in listRow:
			if '&' in data:
				data1 = string_split(data,'&')
				string += '%10s%10s' %(data1[0],'&'+data1[1]) 
			else:
				string += '%10s' %(data)
		return string
	
	def PartInfo(self,part):
		string = '$'
		isCount = 0
		if hasattr(self,'SECTION_SHELL'):
			for i in self.SECTION_SHELL:
				if part[1] == i[0]:
					string += self.DynaFormat1(i)+'\n$'
					isCount = 1
				elif isCount == 1:
					string += self.DynaFormat1(i)
					isCount = 0
		if hasattr(self,'SECTION_SOLID'):
			for i in self.SECTION_SOLID:
				if part[1] == i[0]:
					string += self.DynaFormat1(i)
		return string
	
	def CheckWrite(self,keywords):
		fout = open(self.src + '\\' + self.checkresult,'w')
#			cmd =  "fout.write(' '.join(" + 'self.' + kw+ "))"
		for i in dir(self):
			if i in keywords:
				fout.write('*'+i+'\n')
				string = ''
				for j in self.__dict__[i]:
					string = self.DynaFormat1(j)
					fout.write(string+"\n")
					if len(j)>2:
						string = self.PartInfo(j)
						fout.write(string+"\n")
				fout.write("$"*80+'\n')
			else:
				pass
		fout.close()
		
		
		
class OptistructInfo(basic):

	@property
	def ParsFEM(self):
		isDuplicate = 0
		for line in open(self.src):
			if '$' not in line:
				if ',' in line :
					data = string_split(line[:-1],',')
				else:
					data = string_split(line[:-1],' ')

			else:
				continue
			keyword = 'self.' + data[0]
			if data[0] in dir(self):
				isDuplicate = 1
			else:
				isDuplicate = 0
				cmd = keyword + '=[]'
				print cmd
				exec(cmd)
			
			if isDuplicate == 1:
					ent = '\n'
					cmd = keyword + ".extend([ent])"
					exec (cmd)
					cmd = keyword + '.extend(data[1:])'
					exec (cmd)
					isDuplicate = 0
			else:
				exec (keyword + '.extend(data[1:])')
				
	@statement
	def ParsPCH(self,keyword,isdbfile=0):
		'''
		keyword: str, punch file keyword
		sidbfile: 0 or 1,output .db file
		'''
		self.res = []
		res_G = {}
		isKeyword = 1
		res_title = ''
		grid_num = '99999999999'
		keyword_num = 1
		finp = open(self.src,'rb')

		c1 = 1. - 2.*0.05*0.05 
		c2 = 4*0.05*0.05*(0.05*0.05 - 1)
		if isdbfile == 1:
			conn = sqlite3.connect(self.src+".db")
			conn.execute("create table if not exists rst(id integer primary key not null, Node not null, x real,y real,z real)")
		
		for line in open(self.src,'rb'):
			data = string_split(line[:-1],' ')
		
			'''
			print  'finp.readline()'
			while True:
				line = finp.readline()
				if not line :
					break
				data = string_split(line[:-1],' ')
			'''
			'''
			print  'lines = finp.readlines()'
			lines = finp.readlines()
			for line in lines:
			data = string_split(line[:-1],' ')
			'''
		# while True:
				# line = finp.readline()
				# if not line :
					# break
				# data = string_split(line[:-1],' ')
				
			if '$' in line and isKeyword==1:# check keyword
				if keyword in line :
					Freq = np.sqrt(float(data[2]))/2/np.pi
					listVector = []
			elif '$' in line and isKeyword==0:
				isKeyword = 1 
				MaxVector = max(listVector)
				PHI = MaxVector /1.25
				if PHI > 0.1248:
					AllowableTestFreq_n = Freq*(np.sqrt(c1 -  np.sqrt(c2+ PHI *PHI))) 
				else:
					AllowableTestFreq_n  = 9999999
				cmd = 'self.res.append([keyword_num,Freq,MaxVector,AllowableTestFreq_n])'

				exec(cmd)
				keyword_num += 1
				
			else:
				isKeyword = 0 
				if len(data) > 0:
					if 'CONT' not in line :
						grid_num = data[0]
						temp = [float(i) for i in data[2:] ]
						res_G[grid_num] = disp_mag(temp)
						listVector.extend(temp)
						if isdbfile == 1:
							# Creat .db file with sqlite3
							dbcommand = "INSERT INTO rst (Node,x,y,z) VALUES (%i,%f,%f,%f)" %(int(grid_num),temp[0],temp[1],temp[2])
							conn.execute(dbcommand);
							
		if isdbfile == 1:
			conn.commit()
			conn.close()
			
		cmd = 'self.res.append([keyword_num,Freq,MaxVector,AllowableTestFreq_n])'
		exec(cmd)
 
if __name__ == '__main__':   
	# # test for frequency
	# starttime = datetime.datetime.now()
	# print starttime
	# PATH = r'C:\temp\bigdata'
	# FILE = '\ESR.pch'
	# TestFile = OptistructInfo(PATH+FILE)

	# TestFile.ParsPCH('EIGENVALUE',0)
	# endtime = datetime.datetime.now()
	# print endtime

	# print (endtime - starttime)
	
	# PltData = pd.DataFrame(TestFile.res,columns = ['Order','Frequence','maxVector','AllowableTestFrequence'])
	# res_plot = CurvePlot(' ','Order','maxVector','r',1,1,111,PltData[ ['Order','maxVector']])
	# res_plot.frame
	# res_plot.maxmin()
	# # pic = PATH+FILE
	# plt.show()
	# # plt.savefig(pic,dpi=100)
	# print 'The allowable test frequence: %f Hz.' %(min(PltData.AllowableTestFrequence))
	# # test for file find
	GeomFile =  DynaInfo('Y:\\cal\\01_Comp\\04_SB\\000_allen\\test\\F1\\Geometry.key')
	GeomFile.Pars
	
