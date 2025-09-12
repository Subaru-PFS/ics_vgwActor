from astropy import units
from astropy.coordinates import Angle
import fitsio
import numpy
import pfswcs


def export(input_file=None, output_file=None, center=None, guide_objects=None, detected_objects=None, identified_objects=None):

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
                header['RA2000'] = Angle(ra, unit=units.deg).to_string(unit=units.hourangle, sep=':', precision=3, pad=True)
                header['DEC2000'] = Angle(dec, unit=units.deg).to_string(sep=':', precision=2, alwayssign=True, pad=True)
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
                ofits.write(guide_objects, units=['', 'degree', 'degree', '', '', 'pix', 'pix', 'mm', 'mm', '', ''], extname='guide_objects')
            if detected_objects is not None:
                ofits.write(detected_objects, units=['', '', '', 'pix', 'pix', '', '', '', 'pix', 'pix', '', '', ''], extname='detected_objects')
            if identified_objects is not None:
                # 'detected_object_id', 'guide_object_id',
                # 'detected_object_x_mm', 'detected_object_y_mm',
                # 'guide_object_x_mm', 'guide_object_y_mm',
                # 'guide_object_x_pix', 'guide_object_y_pix',
                # 'detected_object_x_pix', 'detected_object_y_pix',
                # 'agc_camera_id', 'valid'
                ofits.write(identified_objects, units=['', '', 'mm', 'mm', 'mm', 'mm', 'pix', 'pix', 'pix', 'pix', '', ''], extname='identified_objects')


if __name__ == '__main__':

    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('--design-id', type=int, required=True, help='design identifier')
    parser.add_argument('--frame-id', type=int, required=True, help='frame identifier')
    parser.add_argument('--input-file', required=True, help='')
    parser.add_argument('--output-file', required=True, help='')
    args, _ = parser.parse_known_args()

    from opdb import opDB as opdb

    _, ra, dec, pa, *_ = opdb.query_pfs_design(pfs_design_id=args.design_id)
    pa %= 360
    if pa >= 180:
        pa -= 360

    import field_acquisition

    _, _, _, _, _, _, *values = field_acquisition.acquire_field(design=(args.design_id, None), frame_id=args.frame_id)
    guide_objects, detected_objects, identified_objects, *_ = values
    _guide_objects = numpy.array(
        [
            (x[0], x[1], x[2], x[3]) for x in guide_objects
        ],
        dtype=[
            ('source_id', numpy.int64),  # u8 (80) not supported by FITSIO
            ('ra', numpy.float64),
            ('dec', numpy.float64),
            ('mag', numpy.float32)
        ]
    )
    _detected_objects = numpy.array(
        detected_objects,
        dtype=[
            ('camera_id', numpy.int16),
            ('spot_id', numpy.int16),
            ('moment_00', numpy.float32),
            ('centroid_x', numpy.float32),
            ('centroid_y', numpy.float32),
            ('central_moment_11', numpy.float32),
            ('central_moment_20', numpy.float32),
            ('central_moment_02', numpy.float32),
            ('peak_x', numpy.uint16),
            ('peak_y', numpy.uint16),
            ('peak', numpy.uint16),
            ('background', numpy.float32),
            ('flags', numpy.uint8)
        ]
    )
    _identified_objects = numpy.array(
        [
            (x[0], x[1], x[2], -x[3], x[4], -x[5], x[6], x[7]) for x in identified_objects
        ],
        dtype=[
            ('detected_object_id', numpy.int16),
            ('guide_object_id', numpy.int16),
            ('detected_object_x', numpy.float32),
            ('detected_object_y', numpy.float32),
            ('guide_object_x', numpy.float32),
            ('guide_object_y', numpy.float32),
            ('guide_object_xdet', numpy.float32),
            ('guide_object_ydet', numpy.float32)
        ]
    )
    export(args.input_file, args.output_file, (ra, dec, pa), _guide_objects, _detected_objects, _identified_objects)
