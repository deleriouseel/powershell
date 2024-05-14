#!/bin/bash

#move to correct folder
cd ~/public_html/media/

#loop through names.txt
for bookname in $(cat names.txt);

do
#delete old folder
#rm $bookname.zip

#change to folder with mp3s in it 
cd ~/public_html/media/rafiles

#appends newest file to zip
zip -FS ../$bookname.zip ./$bookname* $(basename $PWD)

done

#how many files in rafiles
#ls | grep $bookname | wc -l

#how many files in zip
#zipinfo -l ../$bookname.zip | wc -l  
#this will be 3 more than ls
