echo $1
gs -sDEVICE=pdfwrite -sOutputFile=saps-vel-plot.pdf -dUseArtBox -dNOPAUSE -dEPSCrop -c "<</Orientation 2>> setpagedevice" -f $1.ps -c quit
pdfcrop saps-vel-plot.pdf
mv saps-vel-plot-crop.pdf saps-vel-plot.pdf
cp saps-vel-plot.pdf saved-plots/$1.pdf
pdftocairo -png saps-vel-plot.pdf
convert -delay 100 frames -loop 0 saps-vel-plot-*.png $1.gif
rm *.png
mv $1.gif movies/