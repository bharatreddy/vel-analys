# echo $1
# gs -sDEVICE=pdfwrite -sOutputFile=jo-plot.pdf -dUseArtBox -dNOPAUSE -dEPSCrop -c "<</Orientation 2>> setpagedevice" -f $1.ps -c quit
# pdfcrop jo-plot.pdf
# mv jo-plot-crop.pdf jo-plot.pdf
# cp jo-plot.pdf saved-plots/$1.pdf
# pdftocairo -png jo-plot.pdf
# convert -delay 100 frames -loop 0 jo-plot-*.png $1.gif
# rm *.png
# mv $1.gif movies/
for file in saved-plots/*.pdf
do

 	echo "file input---> $file"
 	fType="$( cut -d '-' -f 4 <<< "$file" )";
 	fDateExt="$( cut -d '-' -f 5 <<< "$file" )";
 	fDate="$( cut -d '.' -f 1 <<< "$fDateExt" )";
 	dirName="$fDate-$fType"
 	echo "creating directory---> $dirName"
 	mkdir -p pngs/$dirName
 	cp $file pngs/$dirName
 	newFile="$( cut -d '/' -f 2 <<< "$file" )";
 	pdftocairo -png pngs/$dirName/$newFile pngs/$dirName/$fDate-$fType
 	rm pngs/$dirName/$newFile
 # 	fNArr=$(echo $file | tr "-" "\n")
	# for fn in $fNArr
	# do
	#     echo "> $fn"
	#     echo ${fNArr}[0]
	# done
	# break

done
