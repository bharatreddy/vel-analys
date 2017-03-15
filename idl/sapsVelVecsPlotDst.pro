pro sapsVelVecsPlotDst


fNameSP = "/home/bharatr/Docs/data/sapsVelsMagnAzimDst.txt"

rad_load_colortable,/leicester


nel_arr_all = 10000
normMLTArr = fltarr(nel_arr_all)
mltArr = fltarr(nel_arr_all)
mlatArr = fltarr(nel_arr_all)
velMagnArr = fltarr(nel_arr_all)
velAzimArr = fltarr(nel_arr_all)
dstMedianArr = intarr(nel_arr_all)
dstBinArr = fltarr(nel_arr_all)



nv=0
OPENR, 1, fNameSP
WHILE not eof(1) do begin
    READF,1,currNormMLT, currLat, currVelMagn, currVelAzim, currMLATEnd, currMLTEnd, dst_median 

    print, currNormMLT, currLat, currVelMagn, currVelAzim, currMLATEnd, currMLTEnd, dst_median 


    normMLTArr[nv] = currNormMLT
    if ( currNormMLT lt 0.) then begin
    	currMLT = currNormMLT + 24.
    endif else begin
    	currMLT = currNormMLT
    endelse
	mltArr[nv] = currMLT
	mlatArr[nv] = currLat
	velMagnArr[nv] = currVelMagn
	velAzimArr[nv] = currVelAzim
	dstMedianArr[nv] = dst_median

    if ( dst_median eq -96) then $
    	dstBinArr[nv] = "-150 < dst < -75"
    if ( dst_median eq -55) then $
    	dstBinArr[nv] = "-75 < dst < -50"
    if ( dst_median eq -37) then $
    	dstBinArr[nv] = "-50 < dst < -25"
    if ( dst_median eq -19) then $
    	dstBinArr[nv] = "-25 < dst < -10"
    if ( dst_median eq -6) then $
    	dstBinArr[nv] = "-10 < dst < 10"
    

    nv=nv+1   
ENDWHILE         
close,1


normMLTArr = normMLTArr[0:nv-1] 
mltArr = mltArr[0:nv-1] 
mlatArr = mlatArr[0:nv-1]
velMagnArr = velMagnArr[0:nv-1] 
velAzimArr = velAzimArr[0:nv-1] 
dstMedianArr = dstMedianArr[0:nv-1]
dstBinArr = dstBinArr[0:nv-1]

;; get the indices of data in different groups
jindsDst15075 = where( ( ( dstMedianArr eq -96. ) )  )
jindsDst7550 = where( ( ( dstMedianArr eq -55. ) )  )
jindsDst5025 = where( ( ( dstMedianArr eq -37. ) )  )
jindsDst2510 = where( ( ( dstMedianArr eq -19. ) )  )
jindsDst1010 = where( ( ( dstMedianArr eq -6. ) )  )


;; plot the data

;; set a few parameters for the plot
date = 20110403
time = 0400
coords = 'mlt'
hemisphere = 1.
xrangePlot = [-44, 44]
yrangePlot = [-44,20]
velScale = [0,1200.]
factor = 800.
fixed_length = -1
symsize = 0.15
load_usersym, /circle

if coords eq "mlt" then in_mlt=1

ps_open,'/home/bharatr/Docs/plots/saps-vel-vecs.ps'

map_plot_panel,date=date,time=time,coords=coords,/no_fill,xrange=xrangePlot,yrange=yrangePlot,/no_coast,pos=define_panel(2,3,0.5,2,/bar),/isotropic,grid_charsize='0.5',/north, $
	title = "-150 < Dst < -75", charsize = 0.5

currSapsVelMagns = velMagnArr[jindsDst15075]
currSapsVelAzims = velAzimArr[jindsDst15075]
currSapsMlats = mlatArr[jindsDst15075]
currSapsMlts = mltArr[jindsDst15075]

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


		;vec_col = get_black()
		vec_col = get_color_index(vel,scale=velScale,colorsteps=get_colorsteps(),ncolors=get_ncolors(), param='power')

		oplot, [x_pos_vec], [y_pos_vec], psym=8, $
			symsize=symsize, color=vec_col, noclip=0

		oplot, [x_pos_vec,new_x], [y_pos_vec,new_y],$
				thick=2, COLOR=vec_col, noclip=0

	endfor

map_plot_panel,date=date,time=time,coords=coords,/no_fill,xrange=xrangePlot,yrange=yrangePlot,/no_coast,pos=define_panel(2,3,1,1,/bar),/isotropic,grid_charsize='0.5',/north, $
	title = "-75 < Dst < -50", charsize = 0.5


currSapsVelMagns = velMagnArr[jindsDst7550]
currSapsVelAzims = velAzimArr[jindsDst7550]
currSapsMlats = mlatArr[jindsDst7550]
currSapsMlts = mltArr[jindsDst7550]

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


		;vec_col = get_black()
		vec_col = get_color_index(vel,scale=velScale,colorsteps=get_colorsteps(),ncolors=get_ncolors(), param='power')

		oplot, [x_pos_vec], [y_pos_vec], psym=8, $
			symsize=symsize, color=vec_col, noclip=0

		oplot, [x_pos_vec,new_x], [y_pos_vec,new_y],$
				thick=2, COLOR=vec_col, noclip=0

	endfor


map_plot_panel,date=date,time=time,coords=coords,/no_fill,xrange=xrangePlot,yrange=yrangePlot,/no_coast,pos=define_panel(2,3,0,1,/bar),/isotropic,grid_charsize='0.5',/north, $
	title = "-50 < Dst < -25", charsize = 0.5

currSapsVelMagns = velMagnArr[jindsDst5025]
currSapsVelAzims = velAzimArr[jindsDst5025]
currSapsMlats = mlatArr[jindsDst5025]
currSapsMlts = mltArr[jindsDst5025]

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


		;vec_col = get_black()
		vec_col = get_color_index(vel,scale=velScale,colorsteps=get_colorsteps(),ncolors=get_ncolors(), param='power')

		oplot, [x_pos_vec], [y_pos_vec], psym=8, $
			symsize=symsize, color=vec_col, noclip=0

		oplot, [x_pos_vec,new_x], [y_pos_vec,new_y],$
				thick=2, COLOR=vec_col, noclip=0

	endfor


map_plot_panel,date=date,time=time,coords=coords,/no_fill,xrange=xrangePlot,yrange=yrangePlot,/no_coast,pos=define_panel(2,3,1,0,/bar),/isotropic,grid_charsize='0.5',/north, $
	title = "-25 < Dst < -10", charsize = 0.5

currSapsVelMagns = velMagnArr[jindsDst2510]
currSapsVelAzims = velAzimArr[jindsDst2510]
currSapsMlats = mlatArr[jindsDst2510]
currSapsMlts = mltArr[jindsDst2510]

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


		;vec_col = get_black()
		vec_col = get_color_index(vel,scale=velScale,colorsteps=get_colorsteps(),ncolors=get_ncolors(), param='power')

		oplot, [x_pos_vec], [y_pos_vec], psym=8, $
			symsize=symsize, color=vec_col, noclip=0

		oplot, [x_pos_vec,new_x], [y_pos_vec,new_y],$
				thick=2, COLOR=vec_col, noclip=0

	endfor


map_plot_panel,date=date,time=time,coords=coords,/no_fill,xrange=xrangePlot,yrange=yrangePlot,/no_coast,pos=define_panel(2,3,0,0,/bar),/isotropic,grid_charsize='0.5',/north, $
	title = "-10 < Dst < 10", charsize = 0.5

currSapsVelMagns = velMagnArr[jindsDst1010]
currSapsVelAzims = velAzimArr[jindsDst1010]
currSapsMlats = mlatArr[jindsDst1010]
currSapsMlts = mltArr[jindsDst1010]

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


		;vec_col = get_black()
		vec_col = get_color_index(vel,scale=velScale,colorsteps=get_colorsteps(),ncolors=get_ncolors(), param='power')

		oplot, [x_pos_vec], [y_pos_vec], psym=8, $
			symsize=symsize, color=vec_col, noclip=0

		oplot, [x_pos_vec,new_x], [y_pos_vec,new_y],$
				thick=2, COLOR=vec_col, noclip=0

	endfor


plot_colorbar, 1., 1., 0., 0., /square, scale=velScale, parameter='power', legend='SAPS Velocity [m/s]'

ps_close, /no_filename


end