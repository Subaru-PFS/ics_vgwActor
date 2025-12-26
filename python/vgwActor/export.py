import fitsio
from astropy import units
from astropy.coordinates import Angle

import pfswcs


def export(input_file=None, output_file=None, center=None, guide_objects=None, detected_objects=None,
           identified_objects=None
           ):

    # field center
    if center is not None:
        ra, dec, pa = center
        # wcs (sip)
        wcs = pfswcs.agcwcs_sip(ra, dec, pa)
    with fitsio.FITS(input_file) as ifits:
        with fitsio.FITS(output_file, 'rw', clobber=True) as ofits:
            # primary
            hdu = ifits[0]
            data = hdu.read()
            header = hdu.read_header()
            if center is not None:
                header['RA2000'] = Angle(ra, unit=units.deg).to_string(
                    unit=units.hourangle, sep=':', precision=3, pad=True
                )
                header['DEC2000'] = Angle(dec, unit=units.deg).to_string(
                    sep=':', precision=2, alwayssign=True, pad=True
                )
                header['RA'] = header['RA2000']
                header['DEC'] = header['DEC2000']
                header['EQUINOX'] = 2000.0
                header['INST-PA'] = pa
            ofits.write(data, header=header)
            # extensions (images)
            for hdu in ifits[1:]:
                data = hdu.read()
                if data is None:
                    continue
                header = hdu.read_header()
                extname = header['EXTNAME']
                if extname in ('CAM1', 'CAM2', 'CAM3', 'CAM4', 'CAM5', 'CAM6'):
                    icam = int(extname[3:]) - 1
                    if center is not None:
                        h = wcs[icam].to_header(relax=True)
                        for k, nk in (('PC1_1', 'CD1_1'), ('PC1_2', 'CD1_2'), ('PC2_1', 'CD2_1'), ('PC2_2', 'CD2_2')):
                            if k in h:
                                header[nk] = h[k]
                        for k in h:
                            if k.startswith(('CRPIX', 'CRVAL', 'CTYPE', 'CUNIT', 'A_', 'AP_', 'B_', 'BP_')):
                                header[k] = h[k]
                    ofits.write(data, compress='rice', header=header, extname=extname)
                else:
                    ofits.write(data, header=header, extname=extname)
            # extensions (binary tables)
            if guide_objects is not None:
                ofits.write(
                    guide_objects, units=['', 'degree', 'degree', '', '', 'pix', 'pix', 'mm', 'mm', '', ''],
                    extname='guide_objects'
                )
            if detected_objects is not None:
                ofits.write(
                    detected_objects, units=['', '', '', 'pix', 'pix', '', '', '', 'pix', 'pix', '', '', ''],
                    extname='detected_objects'
                )
            if identified_objects is not None:
                # 'detected_object_id', 'guide_object_id',
                # 'detected_object_x_mm', 'detected_object_y_mm',
                # 'guide_object_x_mm', 'guide_object_y_mm',
                # 'guide_object_x_pix', 'guide_object_y_pix',
                # 'detected_object_x_pix', 'detected_object_y_pix',
                # 'agc_camera_id', 'valid'
                ofits.write(
                    identified_objects, units=['', '', 'mm', 'mm', 'mm', 'mm', 'pix', 'pix', 'pix', 'pix', '', ''],
                    extname='identified_objects'
                )


if __name__ == '__main__':

    from argparse import ArgumentParser
    import numpy as np

    from pfs.utils.database.opdb import OpDB
    from agActor import field_acquisition
    from agActor.utils import data

    parser = ArgumentParser()
    parser.add_argument('--frame-id', type=int, required=True, help='frame identifier')
    parser.add_argument('--input-file', required=True, help='')
    parser.add_argument('--output-file', required=True, help='')
    parser.add_argument('--design-id', type=int, required=False, help='design identifier')
    parser.add_argument('--dsn', default=None, help='database DSN')
    args, _ = parser.parse_known_args()

    opdb = OpDB(args.dsn)
    OpDB.set_default_connection(host=opdb.host, port=opdb.port, user=opdb.user, dbname=opdb.dbname)

    print(f'Querying frame information for {args.frame_id}...', end='', flush=True)
    frame_info = data.query_agc_exposure(args.frame_id)
    if frame_info is None:
        raise RuntimeError(f'No frame information found for frame ID {args.frame_id}')
    kwargs = {
        'taken_at': frame_info.taken_at,
        'adc': frame_info.adc_pa,
        'inr': frame_info.insrot,
        'm2_pos3': frame_info.m2_pos3,
        'max_residual': 1
    }

    if args.design_id is None:
        args.design_id = frame_info.pfs_design_id
    print(f' done. Design ID: {args.design_id}')

    print('Fetching design information...', end='', flush=True)
    sql = 'SELECT ra_center_designed, dec_center_designed, pa_designed FROM pfs_design WHERE pfs_design_id = :design_id'
    ra, dec, pa = opdb.query_array(sql, params={'design_id': args.design_id})[0]
    print(f' done. RA: {ra}, Dec: {dec}, PA: {pa}')

    pa %= 360
    if pa >= 180:
        pa -= 360

    print('Acquiring field...', end='', flush=True)
    guide_catalog = field_acquisition.acquire_field(design_id=args.design_id, frame_id=args.frame_id, **kwargs)
    print(
        f" done. Found {len(guide_catalog.guide_objects)} guide objects, "
        f"{len(guide_catalog.detected_objects)} detected objects, "
        f"and {len(guide_catalog.identified_objects)} identified objects."
    )

    # Add the negatives (see ticket)
    guide_catalog.identified_objects.loc[:, 'guide_object_y_mm'] *= -1
    guide_catalog.identified_objects.loc[:, 'detected_object_y_mm'] *= -1

    # Get the objects.
    guide_objects = np.array(guide_catalog.guide_objects)
    detected_objects = np.array(guide_catalog.detected_objects)
    identified_objects = np.array(guide_catalog.identified_objects)

    # Export the file.
    print('Exporting file...')
    export(args.input_file, args.output_file, (ra, dec, pa), guide_objects, detected_objects, identified_objects)
