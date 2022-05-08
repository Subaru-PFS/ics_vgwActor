import numpy
from astropy import wcs


def agcwcs_sip(ra, dec, inst_pa):

    scale = 1.00  # unknown scale parameter

    cx2 = 1.43748020e-02
    cx7 = -1.88232442e-04
    s = 0.013 / 270.0
    t = cx2 - 2 * cx7
    u = 3 * s ** 2 * cx7 / t

    dx2 = 2.62647800e02
    dx7 = 3.35086900e00
    sig = 0.013 / 270.0 * t / 0.014
    tau = dx2 - 2 * dx7
    ups = 3 * sig ** 2 * dx7 / tau

    pa = numpy.deg2rad(-(inst_pa - 90.0) + numpy.array([0, 60, 120, 180, 240, 300]))

    CD1_1 = numpy.rad2deg(-s * scale * t * numpy.sin(pa))
    CD1_2 = numpy.rad2deg(s * scale * t * numpy.cos(pa))
    CD2_1 = -CD1_2
    CD2_2 = CD1_1

    a = numpy.array([[0, 0, 0, 0], [0, 0, 0, 0], [0, u, 0, 0], [u, 0, 0, 0]])
    b = numpy.array([[0, 0, 0, u], [0, 0, u, 0], [0, 0, 0, 0], [0, 0, 0, 0]])
    ap = numpy.array([[0, 0, 0, 0], [0, 0, 0, 0], [0, ups, 0, 0], [ups, 0, 0, 0]])
    bp = numpy.array([[0, 0, 0, ups], [0, 0, ups, 0], [0, 0, 0, 0], [0, 0, 0, 0]])

    w = [wcs.WCS() for _ in range(6)]

    for i, _w in enumerate(w):
        _w.wcs.crpix = [512.5 + 24, 19075.11538 + 9]
        _w.wcs.ctype = ['RA---TAN-SIP', 'DEC--TAN-SIP']
        _w.wcs.crval = [ra, dec]
        _w.wcs.cunit = ['deg', 'deg']
        _w.wcs.cd = [[CD1_1[i], CD1_2[i]], [CD2_1[i], CD2_2[i]]]
        _w.sip = wcs.Sip(a, b, ap, bp, [512.5 + 24, 19075.11538 + 9])

    return w


if __name__ == '__main__':

    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('ra', help='right ascension (ICRS) of the field center (hr)')
    parser.add_argument('dec', help='declination (ICRS) of the field center (deg)')
    parser.add_argument('--inst-pa', type=float, default=0, help='position angle of the instrument, east of north (deg)')
    args, _ = parser.parse_known_args()

    from astropy import units
    from astropy.coordinates import Angle

    ra = Angle(args.ra, unit=units.hourangle).degree
    dec = Angle(args.dec, unit=units.deg).degree

    w = agcwcs_sip(ra, dec, args.inst_pa)
    for _w in w:
        print(_w.to_header(relax=True))
