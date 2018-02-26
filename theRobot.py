# -*- encoding:utf8 _*-
#from __future__ import unicode_literals
'''
Math Word Problem Solving
https://www.microsoft.com/en-us/research/project/sigmadolphin-2/
'''
import os
from optparse import OptionParser
import urllib2
import json
import copy
from prettytable import PrettyTable
from mako.template import Template

import jieba
jieba.load_userdict('math.dict')
import jieba.posseg as pseg
import regex as re

import sys
import settings
for mpath in settings.OPERN_SOURCE_CODES_DIRS:
    sys.path.append(mpath)
for rcpath in settings.RESOURCE_DIRS:
    sys.path.append(rcpath)

# from zhopenie.extractor import Extractor
# extractor = Extractor()
# extractor.setLTPModelsPath(settings.LTP_MODELS_PATH)
# extractor.load()
# data = '爸爸养了6条红色金鱼，5条彩色金鱼，爸爸总共养了几条鱼？'
# extractor.chunk_str(data)
# extractor.resolve_all_conference()
# print("Triple: ")
# print('\n'.join(str(p) for p in extractor.triple_list).decode('utf8'))

# extractor.release()




class cnprobase():
	def __init__(self):
		pass
	def parse(self, entity):
		url = 'http://knowledgeworks.cn:20314/probaseplus/pbapi/getconcepts?kw={word}'.format(word = entity.encode('utf8'))
		s=urllib2.urlopen(url)
		print s.read().decode('utf8')
class dbPediaCn():
	def __init__(self):
		pass
	def parse(self, entity):
		url = 'http://knowledgeworks.cn:30001/?p={word}'.format(word = entity.encode('utf8'))
		s=urllib2.urlopen(url)
		print s.read().decode('utf8')
thekg = dbPediaCn()
cnpKG = cnprobase()
class NewWord():
	def __init__(self):
		self.word = None
		self.flag = None

class Robot():
	def __init__(self, theOptions):
		self.options = theOptions
		self.minus_verbs = self.loadMinusVerbs()
		###ltp
		# -*- coding: utf-8 -*-
		import os
		LTP_DATA_DIR = '/path/to/your/ltp_data'  # ltp模型目录的路径
		cws_model_path = './/knols//ltp_data//cws.model'  # 分词模型路径，模型名称为`cws.model`
		pos_model_path = './/knols//ltp_data//pos.model'  # 词性标注模型路径，模型名称为`pos.model`
		ner_model_path = './/knols//ltp_data//ner.model'  # 词性标注模型路径，模型名称为`ner.model`
		
		from pyltp import Segmentor
		self.segmentor = Segmentor()  # 初始化实例
		self.segmentor.load(cws_model_path)  # 加载模型
		#words = self.segmentor.segment('元芳你怎么看')  # 分词

		from pyltp import Postagger
		self.postagger = Postagger() # 初始化实例
		self.postagger.load(pos_model_path)  # 加载模型
		
		from pyltp import NamedEntityRecognizer
		self.recognizer = NamedEntityRecognizer() # 初始化实例
		self.recognizer.load(ner_model_path)  # 加载模型
		
	def tableKG(self, mathKG):
		#http://www.lxway.com/46509591.htm
		#https://segmentfault.com/q/1010000008847010
		x = PrettyTable([u"执行者", u"角色[所有者|干预者]", u"物品", u"操作符", u"数量"], encoding=sys.stdout.encoding)
		x.align[u"物品"] = "1" #以姓名字段左对齐
		x.padding_width = 1  # 填充宽度
		
		for owner in mathKG['owners']:
			for wupin in owner['wupin']:
				x.add_row([owner['name'],owner['role'], wupin['name'],wupin['operator'], wupin['amount']])

		print x
		
	def getResultInNatLaguage(self, result, tigan, timu, message= None):
		timu_origin = copy.deepcopy(timu)
		timu = re.sub(u'(？|\?)', u'。', timu)
		
		print tigan.encode('gbk'), timu_origin.encode('gbk')
		if result:
			print u'答:', re.sub(u'(多少|几)', str(result), timu)
		if self.options.debug:
			print message
		# if result== 0:
			# print tgkg['persons'][0]['name'],u'与', tgkg['persons'][1]['name'],u'一样多'
		# if result >0:
			# print tgkg['persons'][0]['name'],u'比', tgkg['persons'][1]['name'],u'多',result
		# if result <0:
			# print tgkg['persons'][0]['name'],u'比', tgkg['persons'][1]['name'],u'少',result
	def assignRoleToPlayers(self, tigan_kg, timu_kg):
		if tigan_kg is None or timu_kg is None:
			return
			
		if len(timu_kg['owners']) ==0:
			for i in range(len(tigan_kg['owners'])):
				if i == 0:
					tigan_kg['owners'][i]['role'] = u'所有者'
				else:
					tigan_kg['owners'][i]['role'] = u'干预者'
	def process(self, question, theOptions, scoringOnly= False):
		tigan = question['robot']['tigan']
		timu = question['robot']['timu']
		
		posTagger = 'jieba'
		tgkg = None
		tgkg_a = self.calc(tigan, 'TIGAN',theOptions, scoringOnly, pos_tag_method=posTagger)

		if len(tgkg_a['owners']) == 0:
			tgkg_b = self.calc(tigan, 'TIGAN',theOptions, scoringOnly, pos_tag_method='ltp')
			if len(tgkg_b['owners']) > 0:
				posTagger = 'ltp'
				tgkg = copy.deepcopy(tgkg_b)
		else:
			tgkg = copy.deepcopy(tgkg_a)
		tmkg = self.calc(timu, 'TIMU', theOptions, scoringOnly, pos_tag_method=posTagger)
		
		self.assignRoleToPlayers(tgkg, tmkg)
		
		self.updateKGOperators(tgkg, tigan)
		
		result = None
		if tgkg is None:
			return result
			
		
		msg = {}

		#result = int(tgkg['owners'][0][attributs[0]]['amount'] - tgkg['owners'][1][attributs[0]]['amount'])
		msg['ower_size'] = len(tgkg['owners'])
		
		result_ex = '0'
		if msg['ower_size'] > 0:
			for number in tgkg['owners'][0]['wupin']:
				result_ex += number['operator'] + str(number['amount'])

		result = eval(result_ex)
		if not scoringOnly:
			print result_ex
			self.getResultInNatLaguage(result, tigan, timu, message = msg)
			self.tableKG(tgkg)
		return result
		

			
	def getMyWords(self, timu, toDoDebug, keepSilent, pos_tag_method='jieba'):
		'''
			pos_tag_method: jieba | ltp
		'''
		if pos_tag_method=='jieba':
			words = pseg.cut(timu)
			myWords = []
			for w in words:
				myWord = NewWord()
				###分词矫正
				if w.word in [u'爸爸',u'妈妈']:
					w.flag = 'nr'
					
				myWord.word = w.word
				myWord.flag = w.flag
				myWords.append(myWord)
			toBeRemoved = []
			for index in range(len(myWords)):
				if myWords[index].flag == 'ns':
					if index -1 >=0:
						if myWords[index-1].flag == 'n':
							myWords[index].word = myWords[index-1].word + myWords[index].word
							toBeRemoved.append(index-1)
			newMyWords = []
			for index in range(len(myWords)):
				if index in toBeRemoved:
					continue
				else:
					newMyWords.append(myWords[index])
			return newMyWords, []
			
		###ltp
		# -*- coding: utf-8 -*-
		debug_msgs = []
		if pos_tag_method == 'ltp':
			words = self.segmentor.segment(timu.encode('utf8'))
			postags = self.postagger.postag(words)
			debug_msgs.append('\t'.join(postags))
			
			myWords = []
			for i in range(len(words)):
				w = words[i]
				myWord = NewWord()
				myWord.word = w.decode('utf8')
				myWord.flag = postags[i]
				myWords.append(myWord)
				#print w.decode('utf8').encode('gbk')
				debug_msgs.append(w.decode('utf8'))
			#netags = self.recognizer.recognize(words, postags)  # 命名实体识别
			return myWords, debug_msgs
	def loadMinusVerbs(self):
		math_kg_file = './/knols//mathKG.json'
		sContent = ''.join(open(math_kg_file, 'r').readlines())
		sContent = sContent.decode('utf8')
		return sContent.split('|')
	def getOperator(self, number, startPosition, timu, theKG):
		
		numberPos = timu.find(number, startPosition)
		endPos = numberPos + len(number)
		theText = timu[startPosition:endPos]
		#minus_verb_str = u'用了|用去了|买了|飞走|送给|拔|败|剥|爆|吃了|完成|拿下来|分给|没来|矮|坳|扒|拔|罢|败|病|擦|裁|残|差|拆|扯|撤|沉|惩|迟|抽|掉|黜|辞|倒|丢|夺|剁|废|分|负|过去|割|刮|化|剪|借|砍|看了|亏|离|漏|掠|抹|免|排|磨|抹|赔|劈|骗|弃|迁|抢|切|取|扫|杀|删|少|失|剩|淘|剔|偷|退|忘|违|误|削|消|逊|湮灭|掩饰|游走|凿|折|遮|坠|啄|走'
		#minus_verbs = minus_verb_str.split('|')
		
		
		rlt = re.search(u'({theMinusPattern})\w*'.format(theMinusPattern = '|'.join(self.minus_verbs)) + number, theText)
		if rlt:
			raw_input(rlt.group(0))
			####disambiguate
			if len(theKG['owners']) == 1:
				if rlt.group().find(u'买了')>=0:
					return endPos + 1, '+'
			return endPos + 1, '-'
		else:
			newText = timu[numberPos:]
			#raw_input(newText.encode('gbk'))
			rlt2 = re.search(number + u'\w*({theMinusPattern})'.format(theMinusPattern = '|'.join(self.minus_verbs)), newText)
			if rlt2:
				return numberPos + len(rlt2.group(0)), '-'
			else:
				return endPos + 1, '+'
	def getEntities(self, words, posTaggingMethod):
		entities = {}
		entities['owner'] = []
		entities['wupin'] = []
		entities['numbers'] = []
		for w in words:
			print w.word,  w.flag
		if posTaggingMethod == 'jieba':
			for w in words:
				
				#nr 人名#s 处所词; #f 方位词#s 处所词#ns 地名 #r 代词
				if w.flag in ['nr', 's', 'f', 'ns', 'r']:
					if not w.word in entities['owner']:
						entities['owner'].append(w.word)
				if w.flag in ['m']:
					entities['numbers']
					if re.search('\d', w.word):
						entities['numbers'].append( w.word)

				if w.flag in ['n', 'nr']:
					if not w.word in entities['wupin']:
						entities['wupin'].append(w.word)
		if posTaggingMethod == 'ltp':
			posTagList = []
			for w in words:
				posTagList.append(w.flag)
			for i in range(len(words)):
				w = words[i]
				if w.flag in ['nh']:
					if not w.word in entities['owner']:
						entities['owner'].append(w.word)
						
				'''爸爸 养 了 6 条 红色 金鱼
					n   v   u m q  n     n
				'''
				if i == 0:
					if words[i+1].flag == 'v':
						entities['owner'].append(w.word)

				
				if w.flag in ['m']:
					if i == 0:
						if words[i+1] == 'q':
							'''一 年 12 个 月'''
							entities['owner'].append(w.word + words[i+1].word)
							continue
				
					entities['numbers']
					if re.search('\d', w.word):
						entities['numbers'].append( w.word)
				if w.flag in ['n', 'nr']:
					if i>=2:
						is_qualified = False
						if words[i-2].flag == 'm' and words[i-1].flag == 'q':
							is_qualified = True
						if words[i-1].flag == 'm' :
							is_qualified = True
						
						if is_qualified:
							if not w.word in entities['wupin']:
								entities['wupin'].append(w.word)
						
				'''
				十一月份 总共 30 天
				'''
				if w.flag in ['nt']:
					entities['owner'].append(w.word)
				
				'''
				一 年 12 个 月 ， 过去 了 10 个 月
			m q m q n
			'''
			if ' '.join(posTagList).find('m q m q') == 0:
				entities['owner'].append(words[0].word + words[1].word)
		####{'owner': [], 'wupin': [u'\u4eba', u'\u620f'], 'numbers': [u'22', u'13']}
		return entities
	def updateKGOperators(self, math_kg, tigan_text):
		if math_kg is None:
			return
			
		for m in range(len(math_kg['owners'])):
			oneOwner = math_kg['owners'][m]
			for n in range(len(oneOwner['wupin'])):
				oneWupin = oneOwner['wupin'][n]
				int_pos = int(oneWupin['number_position'])
				number = oneWupin['amount']
				pos, theOperator = self.getOperator(str(number), int_pos, tigan_text, math_kg)
				#if oneOwner['role'] == 
				math_kg['owners'][m]['wupin'][n]['operator'] = theOperator
	def disabiguateOwners(self, owner_names):
		for prn in [u'他', u'她', u'它', u'他们', u'她们', u'它们']:
			if prn in owner_names:
				pos = owner_names.index(prn)
				if pos >0:
					owner_names.remove(prn)
	def isRealOwnerWupinNumberTriple(self, owner, wupin_name, number, tigan):
		sents = tigan.split(u'，')
		for sent in sents:
			import chardet
			#if owner['name'] in sent and str(number) in sent:
				#bug: 小刚 3 小刚存了43元
				#因为3不属于小刚，但是刚好43字母中含有3，所以误判。
				#因此，上面的if 语句不是一个号的判断。
				#应该将数字都提取出来，然后做判断
			regex=re.compile('\d+')
			allNumbersInSent = regex.findall(sent)
			if owner['name'] in sent and str(number) in allNumbersInSent:
				print owner['name'], number, sent
				raw_input()
				tmpName = u'比' + owner['name']
				if tmpName in sent:
					return False
					
				return True
		return False
	def calc(self, word_math_problem, section, theOptions, scoringOnly, pos_tag_method='jieba'):
		'''
			pos_tag_method: part of speech tagging method
		'''
		kg = {}
		words, debugMsgList = self.getMyWords(word_math_problem, theOptions.debug, scoringOnly, pos_tag_method= pos_tag_method)
		
		entities = self.getEntities(words, pos_tag_method)
		self.disabiguateOwners(entities['owner'])
		#https://wenku.baidu.com/view/03abd6f70508763231121250.html
		kg['owners'] = [] #owner could be person or 处所词或方位词
		
		wupin_name = None
		#草地上3只小鸡在做游戏
		#小鸡 游戏都是wupin,取其一。
		
		####去除与实施者相同的物品
		for ownerName in entities['owner']:
			if ownerName in entities['wupin']:
				entities['wupin'].remove(ownerName)
				
		if len(entities['wupin']) > 0:
			wupin_name = entities['wupin'][0]

		for ownerName in entities['owner']:
			owner = {'name':ownerName, 'role':None}
			if section == 'TIGAN':
				owner['wupin'] = []
				pos = 0
				for number in entities['numbers']:
					if self.isRealOwnerWupinNumberTriple(owner, wupin_name, number, word_math_problem):
					#pos, theOperator = self.getOperator(str(number), pos, timu)
						owner['wupin'].append({'amount':str(number), 'number_position': pos, 'name':wupin_name, 'operator': None})
				kg['owners'].append(owner)


		return kg
		
		
		# entities = {}
		# for item in kg[pos_tag_method]:
			# entities[item] = []
		# #entities['n'] = []
		# #entities['m'] = []
		# #entities['s'] = []  
		# #entities['ns'] = []  
		# #entities['f'] = []  
		# #entities['location'] = []

		# for w in words:
			# if theOptions.debug:
				# if not scoringOnly:
					# print('%s %s' % (w.word, w.flag))
			
			# if entities.has_key(w.flag):
				# if w.flag == 'm': #数字
					# if not re.search('\d', w.word):
						# continue
					# entities[w.flag].append( w.word)
				# else:
					# if not w.word in entities[w.flag]:
						# entities[w.flag].append( w.word)

		# wupin_name = None
		# #草地上3只小鸡在做游戏
		# #小鸡 游戏都是wupin,取其一。
		# if len(entities['n']) > 1:
			# wupin_name = entities['n'][0]
		# #print entities.keys()
		# #https://wenku.baidu.com/view/03abd6f70508763231121250.html
		# kg['owners'] = [] #owner could be person or 处所词或方位词
		# for syntaxLabel in ['nr', 's', 'f', 'ns']:
			# for index in range(len(entities[syntaxLabel])):
				# name = entities[syntaxLabel][index]
				# owner = {'name':name}
				# if section == 'TIGAN':
					# owner['wupin'] = []
					# pos = 0
					# for number in entities['m']:
						# pos, theOperator = self.getOperator(str(number), pos, timu)
						# owner['wupin'].append({'amount':str(number), 'name':wupin_name, 'operator': theOperator})
					# kg['owners'].append(owner)
		
			
		# return kg
def getPunctuationClauses(question):
	words = pseg.cut(question)
	ent = None
	ft = None
	val = None
	
	PClauseList = []
	#punctuation clauses
	PClause = {'text':''}
	for word, flag in words:
		if flag == 'x':
			PClauseList.append(PClause)
			PClause['text'] += word
			
			PClause = {'text':''}
			continue
			
		PClause['text'] += word
	return PClauseList
def parseMathQuestion(questText):
	'''
	This function is used parse the quesiton into tigan and timu.
	分拆题干与设问
	'''
	PClauses = getPunctuationClauses(questText)
	size = len(PClauses)
	tigan = ''
	for clause in PClauses[:-1]:
		tigan += clause['text']
	timu = PClauses[-1]['text']
	return tigan, timu
def do_debugging(quest, options):
	robot.process(quest, options)
	print '-----Done-----'
def getGroundTruthRegisterInfo(tiku_dir):
	register_file = os.path.join(tiku_dir, 'register.txt')
	fin = open(register_file)
	lines = fin.readlines()
	fin.close()
	register_info = {}
	for i in range(1, len(lines)):
		fds = lines[i].strip().split('\t')
		register_info[fds[0]] = {}
		register_info[fds[0]]['status'] = fds[3]
		register_info[fds[0]]['source'] = fds[1]
	return register_info
def buildGroundTruth(tiku_dir):
	regInfo = getGroundTruthRegisterInfo(tiku_dir)
	tiku = []
	size = 1
	for fileName in os.listdir(tiku_dir):
		if not fileName.endswith('.tsv'):
			continue
		id = fileName.strip('.tsv')
		
		if regInfo[id]['status'] == 'Done':
			source = regInfo[id]['source']
			fin = open(os.path.join(tiku_dir, fileName), 'r')
			lines = fin.readlines()
			fin.close()
			
			for line in lines:
				if line.startswith('#'):
					continue
					
				fds = line.decode('utf8').strip().split('\t')
				timu = {}
				timu['source'] = source
				timu['original_text'] = fds[0]
				timu['ans'] = fds[1]
				timu['id'] = size
				tiku.append(timu)
				size += 1
				

	
	gt_file = os.path.join(tiku_dir, 'groundTruths.json')
	sContent = Template(filename="C:\\projects\\mathRobot\\knols\\Templates\\tiku.mako").render(tiku = tiku)
	fgt = open(gt_file, 'w')
	fgt.write(sContent.encode('utf8'))
	fgt.close()
	
			
			
			
if __name__ == '__main__':
	parser = OptionParser()
	parser.add_option("-e", "--evaluate", dest="evaluate", default=False, action="store_true", help="evaluate" )
	parser.add_option("-g", "--gold", dest="gold", default=False, action="store_true", help="build ground truth" )
	parser.add_option("-t", "--test", dest="test", default=False, action="store_true", help="test" )
	parser.add_option("-d", "--debug", dest="debug", default=False, action="store_true", help="debug" )
	parser.add_option("-p", "--pos", dest="pos", help="part of speech tagger methold [jieba|ltp]" )
	(options, args) = parser.parse_args()

	if options.evaluate:
		fgt = open('.//data//tiku//groundTruths.json', 'r')
		sGTs = ''.join(fgt.readlines()).decode('utf8')
		#rint sGTs.encode('gbk')
		fgt.close()
		quests = json.loads(sGTs)
		robot = Robot(options)
		
		total_gold_number = len(quests)
		total_system_number = 0
		for quest in quests:
			print quest['id']
			tigan, timu = parseMathQuestion(quest['original_text'])
			# PClauses = getPunctuationClauses(quest)
			# size = len(PClauses)
			# tigan = ''
			# for clause in PClauses[:-1]:
				# tigan += clause['text']
			#timu = PClauses[-1]['text']
			quest['robot'] = {}
			quest['robot']['tigan'] = tigan
			quest['robot']['timu'] = timu
			

			if options.debug:
				result = robot.process(quest, options, scoringOnly= True)
			else:
				result = robot.process(quest, options)
				print '-----Done-----'
			
			
			try:
				a = float(result)
				b = float(quest['ans'])
			except:
				continue
				
			if float(quest['ans']) == float(result):
				total_system_number += 1
			else:
				if options.debug:
					do_debugging(quest, options)
					raw_input(453)

				
		print 'Tested with {size} word number problem. The Accuracy: {value}%'.format(size = total_gold_number, value = float(total_system_number)/float(total_gold_number)*100)
		

	if options.test:
		#tigan = u'小明有5个苹果，小红有3个苹果，问小明比小红多几个苹果'
		#tigan = u'小明有5个苹果，小红有3个苹果，'
		questText = u'小明有25个苹果，小红有13个苹果，问小明比小红多几个苹果'
		questText = u'从小刚家到学校的路程是2400米，从家走到了学校，忘记带作业，走回到家，再返回学校, 小刚总共走了多少千米'
		questText = u'小明喝了230毫升的雪碧，他又喝100的雪碧, 他总共喝了多少毫升的雪碧？'
		questText = u'原来有22人看戏，又来了13人，现在看戏的有多少人？'
		questText = u'小刚存了43元，小兵存的比小刚少3元， 小兵存了多少钱？'
		#questText = u'班级一共50人，男生有20人，女生有多少人？'
		#questText = u'汽车里有41人，中途有13人上车，车上现在还有多少人？'
		tigan, timu = parseMathQuestion(questText)
		quest= {}
		quest['robot'] = {}
		quest['robot']['tigan'] = tigan
		quest['robot']['timu'] = timu
		robot = Robot(options)
		robot.process(quest, options)
	if options.gold:
		tiku_dir =  './/data//tiku'
		buildGroundTruth(tiku_dir)
		