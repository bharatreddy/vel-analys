pro plot_fit_vels


common radarinfo
common rad_data_blk

fNameSapsVels = "/home/bharatr/Docs/data/apr9data.txt"

; some default settings
velScale = [0., 2000.]
hemisphere = 1.
coords = "mlt"
xrangePlot = [-44, 44]
yrangePlot = [-44,30]
factor = 200.
fixed_length = -1
symsize = 0.35
load_usersym, /circle
rad_load_colortable,/leicester

nel_arr_all = 10000

mltArr = fltarr(nel_arr_all)
latArr = fltarr(nel_arr_all)
velMagnArr = fltarr(nel_arr_all)
velAzimArr = fltarr(nel_arr_all)
dateArr = lonarr(nel_arr_all)
timeArr = intarr(nel_arr_all)
julArr = dblarr(nel_arr_all)

rcnt=0
OPENR, 1, fNameSapsVels
WHILE not eof(1) do begin
	;; read the data line by line

	READF,1, normMLT, mlat, velMagn, velAzim, vMErr, vAErr, dtStr, timeStr
	

	if normMLT lt 0. then begin
		currMLT = normMLT + 24.
	endif else begin
		currMLT = normMLT
	endelse

	currDate = ulong(dtStr)
	currTime = uint(timeStr)
	sfjul,currDate,currTime,currJul

	dateArr[rcnt] = currDate
	timeArr[rcnt] = currTime
	velMagnArr[rcnt] = velMagn
	velAzimArr[rcnt] = velAzim
	mltArr[rcnt] = currMLT
	latArr[rcnt] = mlat
	julArr[rcnt] = currJul

	rcnt += 1

ENDWHILE         
close,1	

dateArr = dateArr[0:rcnt-1]
timeArr = timeArr[0:rcnt-1]
velMagnArr = velMagnArr[0:rcnt-1]
velAzimArr = velAzimArr[0:rcnt-1]
mltArr = mltArr[0:rcnt-1]
latArr = latArr[0:rcnt-1]
julArr = julArr[0:rcnt-1]


; get the uniq times from the arrays
uniqJulsArr = julArr[ uniq(julArr) ]


ps_open, '/home/bharatr/Docs/plots/test-optmzd-fit-apr9.ps'

;; now loop through the uniq elements in the array and plot the data
for jcnt=0,n_elements(uniqJulsArr)-1 do begin
	clear_page
    set_format, /sardi
	; get date time back from the jul value
	currSapsJul = uniqJulsArr[jcnt]
	sfjul, currSapsDate, currSapsTime, currSapsJul, /jul_to_date
	print, "currently working with--->", currSapsDate, currSapsTime

	; get the fitted velocities, azims, mlats and mlts at the selected time
	jindsCurrJuls = where( julArr eq currSapsJul )
	currSapsVelMagns = velMagnArr[jindsCurrJuls]
	currSapsVelAzims = velAzimArr[jindsCurrJuls]
	currSapsMlats = latArr[jindsCurrJuls]
	currSapsMlts = mltArr[jindsCurrJuls]

	map_plot_panel,date=currSapsDate,time=currSapsTime,coords=coords,/no_fill,xrange=xrangePlot, $
        yrange=yrangePlot,/no_coast,pos=define_panel(1,1,0,0,/bar),/isotropic,grid_charsize='0.5',/north, $
        title = string(currSapsDate[0]) + "-" + strtrim( string(currSapsTime[0]), 2), charsize = 0.5

	for vcnt=0,n_elements(currSapsVelMagns)-1 do begin

		lat = currSapsMlats[vcnt]
		plon = currSapsMlts[vcnt]
		vel = currSapsVelMagns[vcnt]
		azim = -90.-1*currSapsVelAzims[vcnt]
		

		lon = ( plon + 360. ) mod 360.

		tmp = calc_stereo_coords(lat, plon, hemisphere=hemisphere, mlt=(coords eq 'mlt') )
		x_pos_vec = tmp[0]
		y_pos_vec = tmp[1]

		vec_azm = azim*!dtor + ( hemisphere lt 0. ? !pi : 0. )
		vec_len = factor*vel/!re/1e3

		; Find latitude of end of vector
		vec_lat = asin( $
			( $
				( sin(lat*!dtor)*cos(vec_len) + $
					cos(lat*!dtor)*sin(vec_len)*cos(vec_azm) $
				) < 1. $
			) > (-1.) $
		)*!radeg

		; Find longitude of end of vector
		delta_lon = ( $
			atan( sin(vec_azm)*sin(vec_len)*cos(lat*!dtor), cos(vec_len) - sin(lat*!dtor)*sin(vec_lat*!dtor) ) $
		)
		lon_rad = plon*!dtor
		if coords eq 'mlt' then $
			vec_lon = (lon_rad + delta_lon)*!radeg/15. $
		else $
			vec_lon = (lon_rad + delta_lon)*!radeg

		; Find x and y position of end of vectors
		tmp = calc_stereo_coords(vec_lat, vec_lon, hemisphere=hemisphere, mlt=(coords eq 'mlt') )
		new_x = tmp[0]
		new_y = tmp[1]

		vec_col = get_color_index(vel,scale=velScale,colorsteps=get_colorsteps(),ncolors=get_ncolors(), param='power')

		oplot, [x_pos_vec], [y_pos_vec], psym=8, $
			symsize=symsize, color=vec_col, noclip=0

		oplot, [x_pos_vec,new_x], [y_pos_vec,new_y],$
				thick=2, COLOR=vec_col, noclip=0

		print, lat, plon, vec_lat, vec_lon, vel, azim

	endfor

	plot_colorbar, 1., 1., 0., 0., /square, scale=velScale, parameter='power', legend='Velocity[m/s]'

	break

endfor


ps_close,/no_filename

end