# -*- coding: utf-8 -*-
"""translate.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1Ix5v5dq-xo0fzh4DVav1HZdUrrz7UQeR
"""

'''from google.colab import drive
!mkdir drive
drive.mount('/content/drive/')'''
directory = "./"

import unicodedata
import re
import torch
import torch.nn as nn
from torch import optim
import torch.nn.functional as F
import random


device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
english_sent = []
french_sent = []

apostrophe = {"It's":"It is","\'re":" are","\'ll":" will","\'m":" am","\'d":" would","She's":"She is","He's":"He is"}
MIN_LENGTH = 5
MAX_LENGTH = 25

def readfile(filename):
  f = open(filename,"r")
  for line in f.readlines():
    temp = line.split("\t")
    french_sent.append(temp[1])
    english_sent.append(temp[0])

  
def remove_accents(text):
    try:
        text = unicode(text, 'utf-8')
    except (TypeError, NameError): # unicode is a default on python 3 
        pass
    text = unicodedata.normalize('NFD', text)
    text = text.encode('ascii', 'ignore')
    text = text.decode("utf-8")
    return str(text)

def replaceapostrophe(string):
  for k,v in apostrophe.items():
    string = re.sub(k,v,string)
  return string

def removepunctuation(sent):
  sent = re.sub('[!?.\']','',sent)
  sent = re.sub('[^0-9a-zA-Z]', ' ', sent)
  return sent

def removepunctuation2(sent):
  

def vocabulary(sentlist):
  listofwords = set()
  listofsent = []
  for sent in sentlist:
    sent = remove_accents(sent.lower())
    sent = replaceapostrophe(sent)
    sent = removepunctuation(sent)
    templist = sent.split()
    setofsent = set(templist)
    listofsent.append(sent)
    listofwords = listofwords.union(setofsent)
  return listofwords, listofsent

device

readfile(directory+"eng-fra.txt")
english_vocab, english_sent = vocabulary(english_sent)
french_vocab, french_sent  = vocabulary(french_sent)
print(len(english_vocab))
english_vocab.add("SOS")
english_vocab.add("EOS")
french_vocab.add("SOS")
french_vocab.add("EOS")
english_vocab = list(english_vocab)
french_vocab  = list(french_vocab)
english_vocab.sort()
french_vocab.sort()
english_vocab = {english_vocab[i]: i for i in range(len(english_vocab))}
french_vocab = {french_vocab[i]: i for i in range(len(french_vocab))}

english_sent_total,french_sent_total = english_sent,french_sent
english_sent = english_sent_total[50000:200000]
french_sent  = french_sent_total[50000:200000]
len(english_sent)

def padding(sent):
  length = sent.shape[1]
  add = torch.zeros(1,MAX_LENGTH - length, device=device, dtype=torch.long)
  return torch.cat((sent,add) dim=1)
  
def makebatches(BATCH_SIZE):
  numbatches = len(english_sent)

def indexesFromSentence(vocab, sentence):
  return [vocab[word] for word in sentence.split()]


def tensorFromSentence(vocab, sentence):
    indexes = indexesFromSentence(vocab, sentence)
    indexes.append(vocab["EOS"])
    return torch.tensor(indexes, dtype=torch.long, device=device).view(1,-1)


def tensorsFromPair(english_vocab, french_vocab, english_sent, french_sent):
    
    input_tensor = tensorFromSentence(english_vocab, english_sent)
    target_tensor = tensorFromSentence(french_vocab, french_sent)
    return (input_tensor, target_tensor)

class EncoderRNN(nn.Module):
    def __init__(self, input_size, hidden_size):
        super(EncoderRNN, self).__init__()
        self.hidden_size = hidden_size
        self.embedding = nn.Embedding(input_size, hidden_size)
        self.gru = nn.GRU(hidden_size, hidden_size)

    def forward(self, input, hidden):
        embedded = self.embedding(input).view(1, 1, -1)
        output = embedded
        output, hidden = self.gru(output, hidden)
        return output, hidden

    def initHidden(self):
        return torch.zeros(1, 1, self.hidden_size, device=device)
      
class DecoderRNN(nn.Module):
    def __init__(self, hidden_size, output_size):
        super(DecoderRNN, self).__init__()
        self.hidden_size = hidden_size
        self.embedding = nn.Embedding(output_size, hidden_size)
        self.gru = nn.GRU(hidden_size, hidden_size)
        self.out = nn.Linear(hidden_size, output_size)
        self.softmax = nn.LogSoftmax(hidden_size, outputsize)
        

    def forward(self, input, hidden):
        output = self.embedding(input).view(1, 1, -1)
        output = F.relu(output)
        output, hidden = self.gru(output, hidden)
        output = self.softmax(self.out(output[0]))
        return output, hidden

    def initHidden(self):
        return torch.zeros(1, 1, self.hidden_size, device=device)

import random

def train(input_tensor, target_tensor, encoder,decoder, encoder_optimizer, decoder_optimizer, criterion):
    
    enchidden = encoder.initHidden()
    encoder_optimizer.zero_grad()
    decoder_optimizer.zero_grad()
    input_length = input_tensor.size(0)
    target_length = target_tensor.size(0)
    encoder_outputs = torch.zeros(max_length, encoder.hidden_size, device=device)
    
    loss = 0
    for ii in range(input_length):
      encoutput, enchidden = encoder.forward(input_tensor[ii],enchidden)
      encoder_outputs[ii] = encoutput[0,0] 
     
    decoder_input = torch.tensor([[french["SOS"]]], device=device)

    decoder_hidden = encoder_hidden
    
    if random.random() < teacher_forcing_ratio:
      use_teacher = True
    else:
      use_teacher = False
    
    if use_teacher:
      for ii in range(target_length):
        output, hidden = decoder.forward(decoder_input, decoder_hidden)
        
    else :
      for ii in range(target_length):
        decoder_output, decoder_hidden = decoder.forward(decoder_input, decoder_hidden)
        topv, topi = decoder_output.topk(1)
        decoder_input = topi.squeeze().detach()
        loss += criterion(decoder_output, target_tensor[di])
        if decoder_input.item() == "EOS":
          break
    
def trainIters(encoder, decoder, n_iters, print_every=1000, plot_every=100, learning_rate=0.01):
    start = time.time()
    print_loss_total = 0  # Reset every print_every
    
    encoder_optimizer = optim.Adam(encoder.parameters(), lr=learning_rate)
    decoder_optimizer = optim.Adam(decoder.parameters(), lr=learning_rate)
    
    training_pairs = [tensorsFromPair(english_vocab, french_vocab, english_sent[i], french_sent[i])
                      for i in range(n_iters)]
    criterion = nn.NLLLoss()

    for iter in range(1, n_iters + 1):
        training_pair = training_pairs[iter - 1]
        input_tensor = training_pair[0]
        target_tensor = training_pair[1]

        loss = train(input_tensor, target_tensor, encoder,
                     decoder, encoder_optimizer, decoder_optimizer, criterion)
        print_loss_total += loss
        plot_loss_total += loss

        if iter % print_every == 0:
            print_loss_avg = print_loss_total / print_every
            print_loss_total = 0
            print('%s (%d %d%%) %.4f' % (timeSince(start, iter / n_iters),
                                         iter, iter / n_iters * 100, print_loss_avg))

        if iter % plot_every == 0:
            plot_loss_avg = plot_loss_total / plot_every
            plot_losses.append(plot_loss_avg)
            plot_loss_total = 0



hiddensize = 100
teacher_forcing_ratio = 0.5
n_iters = 10000
encoder = EncoderRNN(len(english_vocab),100)
decoder = DecoderRNN(len(french_vocab),100)
trainIters(encoder, decoder, 150)
