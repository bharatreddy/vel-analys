pro plot_fit_vels


common radarinfo
common rad_data_blk

fNameSapsVels = "/home/bharatr/Docs/data/apr9data.txt"

; some default settings
velScale = [0., 1500.]
losVelScale = [-1200., 1200.]
hemisphere = 1.
coords = "mlt"
xrangePlot = [-40, 40]
yrangePlot = [-44,0]
factor = 300.
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
timeArr = lonarr(nel_arr_all)
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

	;; for some reason dates are not working well! 
	;; so doing a manual fix by adding 1. Check every time!!!
	currDate = ulong(dtStr)+1
	currTime = uint(timeStr)
	sfjul,currDate,currTime,currJul

	print, "CHECK DATESSSSSS!!!!!!!!---------------->",currDate, currTime, ulong(dtStr)

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


if coords eq "mlt" then in_mlt=1

plotNameDateStr = strtrim( string( dateArr[0] ),2 )























print, "FIRST PLOT!!!!!!!!!"

;; plot mid lat radars only
rad_fan_ids = [209, 208, 33, 207, 206, 205, 204, 32]

ps_open, '/home/bharatr/Docs/plots/' + 'saps-vels-type2-' + plotNameDateStr+ '.ps'

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


    rad_map_overlay_scan, rad_fan_ids, currSapsJul, scale=losVelScale, coords=coords, $
				param = "velocity", AJ_filter = 1, rad_sct_flg_val=2

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
		coLat = (90. - abs(lat))*!dtor
		cos_coLat = (COS(vec_len)*COS(coLat) + $
			SIN(vec_len)*SIN(coLat)*COS(vec_azm) < 1.) > (-1.)
		vec_coLat = ACOS(cos_coLat)
		vec_lat = 90.-vec_coLat*!radeg 

		cos_dLon = ((COS(vec_len) - $
					COS(vec_coLat)*COS(coLat))/(SIN(vec_coLat)*SIN(coLat)) < 1.) > (-1.)
		delta_lon = ACOS(cos_dLon)
		IF vec_azm LT 0 THEN $
			delta_lon = -delta_lon
		vec_lon = (lon*( in_mlt ? 15. : 1. )*!dtor + delta_lon	)*!radeg

		tmp = calc_stereo_coords(vec_lat, vec_lon)
		new_x = tmp[0]
		new_y = tmp[1]


		vec_col = get_black()

		oplot, [x_pos_vec], [y_pos_vec], psym=8, $
			symsize=symsize, color=vec_col, noclip=0

		oplot, [x_pos_vec,new_x], [y_pos_vec,new_y],$
				thick=2, COLOR=vec_col, noclip=0

	endfor

	plot_colorbar, 1., 1.5, 0.4, 0.5, /square, scale=losVelScale, parameter='velocity'

endfor


ps_close,/no_filename

















print, "SECOND PLOT!!!!!!!!!"

ps_open, '/home/bharatr/Docs/plots/' + 'saps-vels-type1-' + plotNameDateStr+ '.ps'

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
		coLat = (90. - abs(lat))*!dtor
		cos_coLat = (COS(vec_len)*COS(coLat) + $
			SIN(vec_len)*SIN(coLat)*COS(vec_azm) < 1.) > (-1.)
		vec_coLat = ACOS(cos_coLat)
		vec_lat = 90.-vec_coLat*!radeg 

		cos_dLon = ((COS(vec_len) - $
					COS(vec_coLat)*COS(coLat))/(SIN(vec_coLat)*SIN(coLat)) < 1.) > (-1.)
		delta_lon = ACOS(cos_dLon)
		IF vec_azm LT 0 THEN $
			delta_lon = -delta_lon
		vec_lon = (lon*( in_mlt ? 15. : 1. )*!dtor + delta_lon	)*!radeg

		tmp = calc_stereo_coords(vec_lat, vec_lon)
		new_x = tmp[0]
		new_y = tmp[1]


		vec_col = get_color_index(vel,scale=velScale,colorsteps=get_colorsteps(),ncolors=get_ncolors(), param='power')

		oplot, [x_pos_vec], [y_pos_vec], psym=8, $
			symsize=symsize, color=vec_col, noclip=0

		oplot, [x_pos_vec,new_x], [y_pos_vec,new_y],$
				thick=2, COLOR=vec_col, noclip=0

	endfor

	plot_colorbar, 1., 1.5, 0.4, 0.5, /square, scale=velScale, parameter='power', legend='Velocity[m/s]'

endfor


ps_close,/no_filename





































end