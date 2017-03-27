pro model_to_radar


common radarinfo
common rad_data_blk

fNameSapsVels = "/home/bharatr/Docs/data/full-model-sample-dst-33.txt"

; some default settings
velScale = [0., 800.]
losVelScale = [-800., 800.]
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

nel_arr_all = 10000

dtStr = lonarr(1)
timeStr = intarr(1)


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

	READF,1, normMLT, mlat, prob_pred, dst_index, velMagn, velAzim
	

	if normMLT lt 0. then begin
		currMLT = normMLT + 24.
	endif else begin
		currMLT = normMLT
	endelse

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
latArr = latArr[0:rcnt-1]
julArr = julArr[0:rcnt-1]


; get the uniq times from the arrays
uniqJulsArr = julArr[ uniq(julArr) ]


if coords eq "mlt" then in_mlt=1

plotNameDateStr = strtrim( string( dateArr[0] ),2 )

;; plot mid lat radars only
rad_fan_ids = [209, 208, 33, 207, 206, 205, 204, 32]
rad_codes = [ "ade", "adw", "cve", "cvw", "fhe", "fhw", "bks", "wal" ]


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
			(*rad_fit_info[data_index]).ngates, year, yrsec, coords=coords, $
			lagfr0=(*rad_fit_data[data_index]).lagfr[scan_beams[0]], $
			smsep0=(*rad_fit_data[data_index]).smsep[scan_beams[0]], $
			fov_loc_full=fov_loc_full, fov_loc_center=fov_loc_center, $
			AZM_FULL = azm_full, AZM_CENTER = azm_center

print, azm_center

print, size(azm_center)

endfor



end