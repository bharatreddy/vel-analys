pro model_to_radar


common radarinfo
common rad_data_blk

fNameSapsVels = "/home/bharatr/Docs/data/full-model-sample-dst-33.txt"

; some default settings
velScale = [0., 800.]
losvelScale = [-1000., 1000.]
param = 'velocity'
hemisphere = 1.
coords = "mlt"
xrangePlot = [-40, 40]
yrangePlot = [-44,20]
factor = 300.
fixed_length = -1
symsize = 0.35
load_usersym, /circle
rad_load_colortable,/website

currDate = 20150105;20130317;
currTime = 0500;2000;
radTimeArr = [ 0400, 0600 ]
exclude = [-20000.,20000.]
nel_arr_all = 10000

dtStr = lonarr(1)
timeStr = intarr(1)


mltArr = fltarr(nel_arr_all)
normMLTArr = fltarr(nel_arr_all)
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

	READF,1, currMLT, mlat, prob_pred, dst_index, velMagn, velAzim
	
	

	if currMLT gt 12. then begin
		normMLT = currMLT - 24.
	endif else begin
		normMLT = currMLT
	endelse

	normMLTArr[rcnt] = normMLT

	;; for some reason dates are not working well! 
	;; so doing a manual fix by adding 1. Check every time!!!
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
normMLTArr = normMLTArr[0:rcnt-1]
latArr = latArr[0:rcnt-1]
julArr = julArr[0:rcnt-1]


; get the uniq times from the arrays
uniqJulsArr = julArr[ uniq(julArr) ]


if coords eq "mlt" then in_mlt=1

plotNameDateStr = strtrim( string( dateArr[0] ),2 )

;; plot mid lat radars only
rad_fan_ids = [209, 208, 33, 207, 206, 205, 204, 32]
rad_codes = [ "ade", "adw", "cve", "cvw", "fhe", "fhw", "bks", "wal" ]

;rad_codes =  [ "fhw" ]

ps_open, '/home/bharatr/Docs/plots/' + 'saps-model-radar-' + plotNameDateStr+ '.ps'


;; now loop through the uniq elements in the array and plot the data
for jcnt=0,n_elements(uniqJulsArr)-1 do begin
	clear_page
    set_format, /sardi
	; get date time back from the jul value
	currSapsJul = uniqJulsArr[jcnt]
	sfjul, currSapsDate, currSapsTime, currSapsJul, /jul_to_date
	print, "currently working with--->", currSapsDate, currSapsTime

	map_plot_panel,date=currSapsDate,time=currSapsTime,coords=coords,/no_fill,xrange=xrangePlot, $
	        yrange=yrangePlot,/no_coast,pos=define_panel(1,1,0,0,/bar),/isotropic,grid_charsize='0.5',/north, $
	        title = string(currSapsDate[0]) + "-" + strtrim( string(currSapsTime[0]), 2), charsize = 0.5


	for rf=0,n_elements(rad_codes)-1 do begin


		rad_fit_read, currDate, rad_codes[rf], time=radTimeArr

		data_index = rad_fit_get_data_index()

		id = (*rad_fit_info[data_index]).id

		sfjul, currDate, currTime, jul

		scan_number = rad_fit_find_scan(jul)

		varr = rad_fit_get_scan(scan_number, groundflag=grnd, $
		param=param, channel=channel, scan_id=scan_id, $
		scan_startjul=jul)

		caldat, jul, mm, dd, year
		yrsec = (jul-julday(1,1,year,0,0,0))*86400.d


		channel = (*rad_fit_info[data_index]).channels[0]
		
		scan_beams = WHERE((*rad_fit_data[data_index]).beam_scan EQ scan_number and $
				(*rad_fit_data[data_index]).channel eq channel, $
				no_scan_beams)

		rad_define_beams, (*rad_fit_info[data_index]).id, (*rad_fit_info[data_index]).nbeams, $
				(*rad_fit_info[data_index]).ngates, year, yrsec, coords="magn", $
				lagfr0=(*rad_fit_data[data_index]).lagfr[scan_beams[0]], $
				smsep0=(*rad_fit_data[data_index]).smsep[scan_beams[0]], $
				fov_loc_full=fov_loc_full, fov_loc_center=fov_loc_center, $
				AZM_FULL = azm_full, AZM_CENTER = azm_center

		;print, azm_center

		;print, size(azm_center)

		sz = size(azm_center, /dim)
		radar_beams = sz[0]
		radar_gates = sz[1]

		for b=0, radar_beams-1 do begin
			for r=0, radar_gates-1 do begin

				;; only plot from those cells which have data
				varr = rad_fit_get_scan(scan_number, $
					param=param, channel=channel, scan_id=scan_id, $
					scan_startjul=jul)

				if n_elements(varr) lt 2 then continue

				szVarr = size(varr)
				if szVarr[2] le r then continue
				if szVarr[1] le b then continue

				if varr[b,r] lt exclude[0] or varr[b,r] gt exclude[1] then $
					continue

				;print, "fov_loc_center--->", fov_loc_center[0,b,r], fov_loc_center[1,b,r]
				;print, "azm_center--->", azm_center[b,r]

				;; identify the nearest vSaps location
				;; convert fov loc center locs to mlt coords
				fov_center_mlat = fov_loc_center[0,b,r]
				fov_center_mlon = fov_loc_center[1,b,r]

				fov_center_mlt = mltdavit(year, yrsec, fov_loc_center[1,b,r])

				if fov_center_mlt ge 12 then begin
					norm_fov_mlt = fov_center_mlt - 24.
				endif else begin
					norm_fov_mlt = 24.
				endelse

				;; check for the nearest MLT
				;jindsNormMlt = where( abs( normMLTArr-norm_fov_mlt ) le 1., cc)

				jindsNormMlt = where( (normMLTArr-norm_fov_mlt le 1.) and (normMLTArr-norm_fov_mlt ge -1.)  , cc)

				if cc eq 0 then begin
					;print, "skipping curr fov cell, NO MLT nearby--->", fov_loc_center[0,b,r], fov_loc_center[1,b,r], fov_center_mlt, norm_fov_mlt
					continue
				endif

				;; check for the nearest MLAT
				currVelMagn = velMagnArr[jindsNormMlt]
				currVelAzim = velAzimArr[jindsNormMlt]
				currVelMLT = mltArr[jindsNormMlt]
				currVelMLAT = latArr[jindsNormMlt]
				
				;jindsMLAT = where( abs( currVelMLAT-fov_center_mlat ) le 1., cc)
				jindsMLAT = where( (currVelMLAT-fov_center_mlat le 1.) and (currVelMLAT-fov_center_mlat ge -1.)  , cc)

				if cc eq 0 then begin
					;print, "skipping curr fov cell, NO MLAT nearby--->", fov_loc_center[0,b,r], fov_loc_center[1,b,r], fov_center_mlt, norm_fov_mlt
					continue
				endif


				minMLTMLAT = currVelMLAT[jindsMLAT]
				minMLTMLT = currVelMLT[jindsMLAT]
				minMLTMagn = currVelMagn[jindsMLAT]
				minMLTAzim = currVelAzim[jindsMLAT]
				ddMLAT = min( abs( minMLTMLAT - fov_center_mlat ), indexMLAT )

				indexMLAT = indexMLAT[0]

				finVelMagn = minMLTMagn[indexMLAT]
				finVelAzim = minMLTAzim[indexMLAT]
				finVelMLT = minMLTMLT[indexMLAT]
				finVelMLAT = minMLTMLAT[indexMLAT]

				;; now estimate the line of sight velocity
				delAzim = ( -90 - finVelAzim ) - azm_center[b,r]
				estLosVel = -1*finVelMagn * cos( delAzim*!dtor ) ;; adjust for component calc

				if finVelMLAT le 50. then $
					print, "FOUND GOOD VALUE--->", finVelMLAT, finVelMLT, estLosVel, finVelMagn, fov_loc_center[0,b,r], fov_center_mlt, azm_center[b,r]
					;print, rad_codes[rf], azm_center[b,r], finVelAzim

				; array for the positions of the corners
				xx = fltarr(4)
				yy = fltarr(4)
				; Convert polar coordinates (latitude and longitude) to cartesian coords
				for p=0, 3 do begin
					lat = fov_loc_full[0,p,b,r]
					lon = mltdavit(year, yrsec, fov_loc_full[1,p,b,r])
					tmp = calc_stereo_coords(lat,lon,mlt=1)
					xx[p] = tmp[0]
					yy[p] = tmp[1]
				endfor
				col = get_color_index(estLosVel, param=param, scale=losvelScale)
				POLYFILL, xx, yy, COL=col, NOCLIP=0

			endfor
		endfor

		

	endfor

	overlay_coast, coords=coords, jul=currSapsJul, /no_fill
    map_overlay_grid, grid_linestyle=0, grid_linethick=1, grid_linecolor=get_gray()

    plot_colorbar, 1., 1.5, 0.4, 0.5, /square, scale=losvelScale, parameter=param, legend='Velocity[m/s]'


endfor

print, (*rad_fit_info[data_index]).nbeams

ps_close,/no_filename

end