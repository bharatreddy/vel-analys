echo $1
gs -sDEVICE=pdfwrite -sOutputFile=jo-plot.pdf -dUseArtBox -dNOPAUSE -dEPSCrop -c "<</Orientation 2>> setpagedevice" -f $1.ps -c quit
pdfcrop jo-plot.pdf
mv jo-plot-crop.pdf jo-plot.pdf
cp jo-plot.pdf saved-plots/$1.pdf
pdftocairo -png jo-plot.pdf
convert -delay 100 frames -loop 0 jo-plot-*.png $1.gif
rm *.png
mv $1.gif movies/