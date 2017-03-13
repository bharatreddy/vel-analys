pro event_saps_vel_data


common radarinfo
common rad_data_blk


coords = "magn"

dateArr = [ 20130622, 20130622, 20130622, 20130622, 20130622, 20130622 ]
radIdArr = [ 32, 33, 204, 205, 206, 207 ]
minTimeArr = [ 0500, 0500, 0500, 0500, 0500, 0500 ]
maxTimeArr = [ 0830, 0830, 0830, 0830, 0830, 0830 ]



; now instead of putting all the data in a single file
; we'll seperate data by event days into seperate files
; then deal with one event/day at a time!!!
baseDir = '/home/bharatr/Docs/data/veldata/'

rcnt = n_elements(dateArr)

for dtRdCnt=0.d,double(rcnt-1) do begin


	if dtRdCnt eq 0.d then begin
		fname_saps_vel = baseDir + 'event-saps-vels-' + strtrim( string(dateArr[dtRdCnt]), 2 ) + '.txt'
		print, 'OPENING FIRST EVENT FILE-->', fname_saps_vel
		openw,1,fname_saps_vel
		workingSapsFileDate = dateArr[dtRdCnt]
	endif else begin
		if workingSapsFileDate ne dateArr[dtRdCnt] then begin
			print, 'CLOSED FILE-->', fname_saps_vel
			close,1
			fname_saps_vel = baseDir + 'saps-vels-' + strtrim( string(dateArr[dtRdCnt]), 2 ) + '.txt'
			print, 'OPENING NEW FILE-->', fname_saps_vel
			openw,1,fname_saps_vel
			workingSapsFileDate = dateArr[dtRdCnt]
		endif
	endelse

	print, "working with---->", dateArr[dtRdCnt], radIdArr[dtRdCnt], minTimeArr[dtRdCnt], maxTimeArr[dtRdCnt]
	date = dateArr[dtRdCnt]
	;; need to check if minTime and maxTime are same. 
	;; In that case we'll just check for next 30 min of
	;; data
	if minTimeArr[dtRdCnt] ne maxTimeArr[dtRdCnt] then begin
		timeRange = [ minTimeArr[dtRdCnt], maxTimeArr[dtRdCnt] ]
	endif else begin
		simMinMaxTime = minTimeArr[dtRdCnt]
		sfjul, date, simMinMaxTime, simMinMaxJuls
		sfjul, dateNew, timeRange, [ simMinMaxJuls, simMinMaxJuls + 30.d/1440.d ],/jul_to_date
		print, "NEW TIME RANGE SET---->", timeRange
	endelse
	radId = radIdArr[dtRdCnt]




	;; get the radar name from id
	radInd = where(network[*].id[0] eq radId, cc)
	if cc lt 1 then begin
		print, ' Radar not in SuperDARN list: '+radar
		rad_fit_set_data_index, data_index-1
		return
	endif
	radCode = network[radInd].code[0]

	print, "radId, radCode--> ", radId, " ", radCode


	rad_fit_read, date, radCode, time=timeRange, /filter


	sfjul,date,timeRange,sjul_search,fjul_search

	dt_skip_time=2.d ;;; we search data the grd file every 2 min
	del_jul=dt_skip_time/1440.d ;;; This is the time step used to read the data --> Selected to be 60 min

	nele_search=((fjul_search-sjul_search)/del_jul)+1 ;; Num of 2-min times to be searched..


	for srch=0.d,double(nele_search-1) do begin

	        ;;;Calculate the current jul
	        juls_curr=sjul_search+srch*del_jul
	    	sfjul,datesel,timesel,juls_curr,/jul_to_date
	    	print, "currently working with-->", datesel,timesel, radCode

	    	;; get index for current data
			data_index = rad_fit_get_data_index()
			if data_index eq -1 then begin
				print, "data index is -1!!!"
				return
			endif

			;; get year and yearsec from juls_curr
			caldat, juls_curr, mm, dd, year
			yrsec = (juls_curr-julday(1,1,year,0,0,0))*86400.d

			;; get scan info
			scan_number = rad_fit_find_scan(juls_curr)
			varr = rad_fit_get_scan(scan_number, scan_startjul=juls_curr)


			;; get mlat, mlon info from fovs
			scan_beams = WHERE((*rad_fit_data[data_index]).beam_scan EQ scan_number and $
						(*rad_fit_data[data_index]).channel eq (*rad_fit_info[data_index]).channels[0], $
						no_scan_beams)

			rad_define_beams, (*rad_fit_info[data_index]).id, (*rad_fit_info[data_index]).nbeams, $
					(*rad_fit_info[data_index]).ngates, year, yrsec, coords=coords, $
					lagfr0=(*rad_fit_data[data_index]).lagfr[scan_beams[0]], $
					smsep0=(*rad_fit_data[data_index]).smsep[scan_beams[0]], $
					fov_loc_full=fov_loc_full, fov_loc_center=fov_loc_center


			mlatArr = (*rad_fit_info[data_index]).mlat
			mlonArr = (*rad_fit_info[data_index]).mlon
			mltArr = mlt(year, yrsec, mlonArr)


			;; get the data
			sz = size(varr, /dim)
			radar_beams = sz[0]
			radar_gates = sz[1]


			; loop through and extract
			for b=0, radar_beams-1 do begin
				for r=0, radar_gates-1 do begin
					if varr[b,r] NE 10000 then begin
						currMLat = fov_loc_center[0,b,r]
						currMlon = fov_loc_center[1,b,r]
						currMLT = mlt(year, yrsec, fov_loc_center[1,b,r])
						;; we'll also need the beam azimuth
						currbeamAzim = rt_get_azim(radCode, b, datesel)
						printf,1, datesel,timesel, b, r, currbeamAzim, varr[b,r], currMLat, currMlon, currMLT, radId, radCode, $
	                                                                format = '(I8, I5, 2I4, f9.4, f11.4, 3f9.4, I5, A5)'

					endif
				endfor
			endfor

	endfor	

endfor

close,1

end