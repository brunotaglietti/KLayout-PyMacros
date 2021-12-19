"""
This file was written by Bruno Taglietti and was based on SiEPIC-Tools and SiEPIC_AMF_PDK
by Jaspreet Jhoja & Mustafa Hammood [SiEPIC Kits Ltd.] and Lukas Chrostowski (c) 2015-2018

Requires: KLayout 0.25 or greater

Component details:
  https://github.com/lukasc-ubc/SiEPIC_AMF_Library/wiki/Circuit-Design-Library-Description


Crash warning:
 https://www.klayout.de/forum/comments.php?DiscussionID=734&page=1#Item_13
 This library has nested PCells. Running this macro with a layout open may
 cause it to crash. Close the layout first before running.

"""

import pya
from pya import DPoint, DPath, Path, Polygon, Point, Text, Trans, Application, LayoutMetaInfo

from SiEPIC.utils import get_technology_by_name

class Db_MMI_RR(pya.PCellDeclarationHelper):
    """
    The PCell declaration for thermally tunable ring filter.
    """

    def __init__(self):
        super(Db_MMI_RR, self).__init__()
        # declare the parameters
        TECHNOLOGY = get_technology_by_name('AMF')
        self.param("silayer", self.TypeLayer, "Si Layer", default=TECHNOLOGY['RIB (10/0@1)'])
        self.param("s", self.TypeShape, "", default=pya.DPoint(0, 0))
        self.param("r", self.TypeDouble, "Radius", default=5)
        self.param("w", self.TypeDouble, "Waveguide Width", default=0.5)
        self.param("MMI_w", self.TypeDouble, "MMI width", default=2)
        self.param("MMI_L", self.TypeDouble, "MMI Length", default=29)
        self.param("MMI_L2", self.TypeDouble, "Secondary MMI Length", default=27)
        self.param("tap_ls", self.TypeDouble, "Taper length", default=10)
        self.param("w_mh", self.TypeInt, "Heater width (nm)", default=3.5)
        self.param("si3layer", self.TypeLayer, "SiEtch2(Rib) Layer", default=TECHNOLOGY['SLAB (12/0@1)'])
        self.param("vllayer", self.TypeLayer, "VL Layer", default=TECHNOLOGY['VIA2 (120/0@1)'])
        self.param("mllayer", self.TypeLayer, "ML Layer", default=TECHNOLOGY['MT2 (125/0@1)'])
        self.param("mhlayer", self.TypeLayer, "MH Layer", default=TECHNOLOGY['HTR (115/0@1)'])
        self.param("textpolygon", self.TypeInt, "Draw text polygon label? 0/1", default=1)
        self.param("textl", self.TypeLayer, "Text Layer", default=TECHNOLOGY['LBL (80/0@1)'])
        self.param("pinrec", self.TypeLayer, "PinRec Layer", default=TECHNOLOGY['PinRec'])
        self.param("devrec", self.TypeLayer, "DevRec Layer", default=TECHNOLOGY['DevRec'])

    def display_text_impl(self):
        # Provide a descriptive text for the cell
        return "Db_MMI_RR"

    def can_create_from_shape_impl(self):
        return False

    def produce_impl(self):
        # This is the main part of the implementation: create the layout
        from math import pi, cos, sin
        from SiEPIC.extend import to_itype

        # fetch the parameters
    #    TECHNOLOGY = get_technology_by_name('GSiP')
        dbu = self.layout.dbu
        ly = self.layout
        shapes = self.cell.shapes

        LayerSi = self.silayer
        LayerSi3 = ly.layer(self.si3layer)
        LayerSiN = ly.layer(LayerSi)
        LayervlN = ly.layer(self.vllayer)
        LayermlN = ly.layer(self.mllayer)
        LayermhN = ly.layer(self.mhlayer)
        TextLayerN = ly.layer(self.textl)
        LayerPinRecN = ly.layer(self.pinrec)
        LayerDevRecN = ly.layer(self.devrec)

        # Define variables for the Modulator
        # Variables for the Si waveguide
        w = to_itype(self.w, dbu)
        r = to_itype(self.r, dbu)

        # Variables for the N layer
        w_1 = 2.0 / dbu  # same for N, P, N+, P+ layer
        r_n = to_itype(self.r - 1.0, dbu)

        # Variables for the VC layer
        w_vc = to_itype(4.0, dbu)
        r_vc1 = to_itype(self.r - 3.75, dbu)
        r_vc2 = to_itype(self.r + 3.75, dbu)

        # Variables for the M1 layer
        w_m1_in = r_vc1 + w_vc / 2.0 + to_itype(0.5, dbu)
        r_m1_in = r_vc1 + w_vc / 2.0 + to_itype(0.5, dbu) / 2.0
        w_m1_out = to_itype(6.0, dbu)
        r_m1_out = to_itype(self.r + 4.25, dbu)

        # Variables for the VL layer
        r_vl = w_m1_in / 2.0 - to_itype(2.1, dbu)
        w_via = to_itype(5.0, dbu)
        h_via = to_itype(5.0, dbu)

        # Variables for the SiEtch2 layer  (Slab)
        w_Si3 = w_m1_out + 2 * (r_m1_out)
        h_Si3 = w_Si3
        taper_bigend = to_itype(2, dbu)
        taper_smallend = to_itype(0.3, dbu)
        taper_length = to_itype(5, dbu)

        # Variables for the MH layer
        w_mh = to_itype(self.w_mh, dbu)
        w_mh_min = 2.0/dbu

        # Define Ring centre
        x0 = r + w / 2
        y0 = r + w

        MMI_L = self.MMI_L/dbu
        MMI_w = self.MMI_w/dbu
        yb_l = 15/dbu
        yb_w = 6/dbu
        tap_w = 0.8 / dbu
        tap_ls = self.tap_ls/dbu

        if tap_ls >= 14/dbu:
            tap_l = tap_ls
        else:
            tap_l = 14/dbu

        Spiral_Dx = 5/dbu

        x_start = x0 - MMI_L/2 - tap_l + Spiral_Dx - 36.5/dbu
        x_end = x0 + MMI_L/2 + tap_l + yb_l + 0.2/dbu

        def vias(x_v, y_v):
            sq_s = 3.0/2
            sq_L = 6.0/2
            boxVL3 = pya.Box(x_v - sq_s / dbu, y_v - sq_s / dbu,
                    x_v + sq_s / dbu, y_v + sq_s / dbu)
            boxMH1 = pya.Box(x_v - sq_L / dbu, y_v - sq_L / dbu,
                x_v + sq_L / dbu, y_v + sq_L / dbu)
            shapes(LayervlN).insert(boxVL3)
            shapes(LayermhN).insert(boxMH1)
            shapes(LayermlN).insert(boxMH1)
            shapes(LayerPinRecN).insert(boxMH1)
            shapes(LayerPinRecN).insert(
                pya.Text("elec2h2", pya.Trans(pya.Trans.R0, x_v, y_v))
            ).text_size = 0.5 / dbu

        #####################
        # Generate the layout:
        # MMI 1


        mmi = pya.Box(x0 - MMI_L/2, y0 + MMI_w / 2,
                      x0 + MMI_L/2, y0 - MMI_w / 2)
        shapes(LayerSiN).insert(mmi)



        # Tapers for MMI 1

        taperTL = pya.Polygon([
                pya.Point(x0 - MMI_L/2 - tap_ls, y0 + MMI_w/4 + w/2),
                pya.Point(x0 - MMI_L/2, y0 + MMI_w/4 + tap_w/2),
                pya.Point(x0 - MMI_L/2, y0 + MMI_w/4 - tap_w/2),
                pya.Point(x0 - MMI_L/2 - tap_ls, y0 + MMI_w/4 - w/2),
        ])
        taperBL = pya.Polygon([
                pya.Point(x0 - MMI_L/2 - tap_l, y0 - MMI_w/4 + w/2),
                pya.Point(x0 - MMI_L/2, y0 - MMI_w/4 + tap_w/2),
                pya.Point(x0 - MMI_L/2, y0 - MMI_w/4 - tap_w/2),
                pya.Point(x0 - MMI_L/2 - tap_l, y0 - MMI_w/4 - w/2),
        ])
        taperTR = pya.Polygon([
                pya.Point(x0 + MMI_L/2 + tap_ls, y0 + MMI_w/4 + w/2),
                pya.Point(x0 + MMI_L/2, y0 + MMI_w/4 + tap_w/2),
                pya.Point(x0 + MMI_L/2, y0 + MMI_w/4 - tap_w/2),
                pya.Point(x0 + MMI_L/2 + tap_ls, y0 + MMI_w/4 - w/2),
        ])
        taperBR = pya.Polygon([
                pya.Point(x0 + MMI_L/2 + tap_l, y0 - MMI_w/4 + w/2),
                pya.Point(x0 + MMI_L/2, y0 - MMI_w/4 + tap_w/2),
                pya.Point(x0 + MMI_L/2, y0 - MMI_w/4 - tap_w/2),
                pya.Point(x0 + MMI_L/2 + tap_l, y0 - MMI_w/4 - w/2),
        ])
        shapes(LayerSiN).insert(taperTL)
        shapes(LayerSiN).insert(taperBL)
        shapes(LayerSiN).insert(taperTR)
        shapes(LayerSiN).insert(taperBR)

        from SiEPIC.utils import arc_wg_xy
        # def arc_wg_xy(x, y, r, w, theta_start, theta_stop, DevRec=None):

        # Connecting arcs - MMI 1 to MMI 2

        arcR = pya.Polygon(arc_wg_xy(
                x0 + MMI_L/2 + tap_ls ,
                y0 + self.r/dbu + MMI_w/4,
                self.r / dbu,
                self.w / dbu,
                -90, 90
        ))
        arcL = pya.Polygon(arc_wg_xy(
                x0 - MMI_L/2 - tap_ls ,
                y0 + self.r/dbu + MMI_w/4,
                self.r / dbu,
                self.w / dbu,
                90, -90
        ))
        shapes(LayerSiN).insert(arcR)
        shapes(LayerSiN).insert(arcL)

        # MMI 2, tapers and ring

        x1 = x0
        y1 = y0 + MMI_w/2 + 2*self.r/dbu

        MMI_L2 = to_itype(self.MMI_L2, dbu)

        mmi2 = pya.Box(x1 - MMI_L2/2, y1 + MMI_w / 2,
                      x1 + MMI_L2/2, y1 - MMI_w / 2)
        shapes(LayerSiN).insert(mmi2)

        taperTL2 = pya.Polygon([
                pya.Point(x1 - MMI_L/2 - tap_ls, y1 + MMI_w/4 + w/2),
                pya.Point(x1 - MMI_L2/2, y1 + MMI_w/4 + tap_w/2),
                pya.Point(x1 - MMI_L2/2, y1 + MMI_w/4 - tap_w/2),
                pya.Point(x1 - MMI_L/2 - tap_ls, y1 + MMI_w/4 - w/2),
        ])
        taperBL2 = pya.Polygon([
                pya.Point(x1 - MMI_L/2 - tap_ls, y1 - MMI_w/4 + w/2),
                pya.Point(x1 - MMI_L2/2, y1 - MMI_w/4 + tap_w/2),
                pya.Point(x1 - MMI_L2/2, y1 - MMI_w/4 - tap_w/2),
                pya.Point(x1 - MMI_L/2 - tap_ls, y1 - MMI_w/4 - w/2),
        ])
        taperTR2 = pya.Polygon([
                pya.Point(x1 + MMI_L/2 + tap_ls, y1 + MMI_w/4 + w/2),
                pya.Point(x1 + MMI_L2/2, y1 + MMI_w/4 + tap_w/2),
                pya.Point(x1 + MMI_L2/2, y1 + MMI_w/4 - tap_w/2),
                pya.Point(x1 + MMI_L/2 + tap_ls, y1 + MMI_w/4 - w/2),
        ])
        taperBR2 = pya.Polygon([
                pya.Point(x1 + MMI_L/2 + tap_ls, y1 - MMI_w/4 + w/2),
                pya.Point(x1 + MMI_L2/2, y1 - MMI_w/4 + tap_w/2),
                pya.Point(x1 + MMI_L2/2, y1 - MMI_w/4 - tap_w/2),
                pya.Point(x1 + MMI_L/2 + tap_ls, y1 - MMI_w/4 - w/2),
        ])

        shapes(LayerSiN).insert(taperTL2)
        shapes(LayerSiN).insert(taperBL2)
        shapes(LayerSiN).insert(taperTR2)
        shapes(LayerSiN).insert(taperBR2)

        arcR2 = pya.Polygon(arc_wg_xy(
                x1 + MMI_L/2 + tap_ls ,
                y1 + self.r/dbu + MMI_w/4,
                self.r / dbu,
                self.w / dbu,
                -90, 90
        ))
        arcL2 = pya.Polygon(arc_wg_xy(
                x1 - MMI_L/2 - tap_ls ,
                y1 + self.r/dbu + MMI_w/4,
                self.r / dbu,
                self.w / dbu,
                90, -90
        ))
        shapes(LayerSiN).insert(arcR2)
        shapes(LayerSiN).insert(arcL2)

        wg_T = pya.Box(x1 - MMI_L/2 - tap_ls, y1 + MMI_w/2 + 2*self.r/dbu - self.w/2/dbu,
                      x1 + MMI_L/2 + tap_ls, y1 + MMI_w/2 + 2*self.r/dbu - 3*self.w/2/dbu
        )
        shapes(LayerSiN).insert(wg_T)

        # Heater arcs

        arcR = pya.Polygon(arc_wg_xy(
                x0 + MMI_L/2 + tap_ls + w_mh/2,
                y0 + self.r/dbu + MMI_w/4,
                (self.r - 1) / dbu,
                3 / dbu,
                -90, 90
        ))
        arcL = pya.Polygon(arc_wg_xy(
                x0 - MMI_L/2 - tap_ls - w_mh/2,
                y0 + self.r/dbu + MMI_w/4,
                (self.r - 1) / dbu,
                3 / dbu,
                90, -90
        ))
        shapes(LayermhN).insert(arcR)
        shapes(LayermhN).insert(arcL)
        arcR2 = pya.Polygon(arc_wg_xy(
                x1 + MMI_L/2 + tap_ls + w_mh/2,
                y1 + self.r/dbu + MMI_w/4,
                (self.r - 1) / dbu,
                3 / dbu,
                -90, 90
        ))
        arcL2 = pya.Polygon(arc_wg_xy(
                x1 - MMI_L/2 - tap_ls - w_mh/2,
                y1 + self.r/dbu + MMI_w/4,
                (self.r - 1) / dbu,
                3 / dbu,
                90, -90
        ))
        shapes(LayermhN).insert(arcR2)
        shapes(LayermhN).insert(arcL2)

        # Connecting heater metal between arcs

        shapes(LayermhN).insert(pya.Box(
            x0 - MMI_L/2 - tap_ls - w_mh_min,
            y0 + 2*self.r/dbu + MMI_w/4 - 2.5/dbu,
            x0 - MMI_L/2 - tap_ls - 0/dbu,
            y0 + 2*self.r/dbu + MMI_w/4 + 3.5/dbu,
        ))
        shapes(LayermhN).insert(pya.Box(
            x0 + MMI_L/2 + tap_ls + w_mh_min,
            y0 + 2*self.r/dbu + MMI_w/4 - 2.5/dbu,
            x0 + MMI_L/2 + tap_ls - 0/dbu,
            y0 + 2*self.r/dbu + MMI_w/4 + 3.5/dbu,
        ))

        # Vias for arc arc heaters connection

        vias(x0 + MMI_L/2 + tap_ls + w_mh/2 - w_mh, y0 + MMI_w/4 - w)
        vias(x0 - MMI_L/2 - tap_ls - w_mh/2 + w_mh, y0 + MMI_w/4 - w)

        # Common ground for arc heater

        shapes(LayermlN).insert(pya.Path([
            pya.Point(x0 + MMI_L/2 + tap_ls + w_mh/2 - 2*w_mh, y0),
            pya.Point(x0 - MMI_L/2 - tap_ls - w_mh/2 + 2*w_mh, y0)], 4/dbu
        ))

        # MMI 2 heater

        shapes(LayermhN).insert(
            pya.Box(
                x0 - MMI_L/2, y0 + MMI_w/2 + 2*r + w_mh/2,
                x0 + MMI_L/2, y0 + MMI_w/2 + 2*r - w_mh/2
            )
        )
        # Vias for MMI 2 heater

        vias(x0 - MMI_L/2, y0 + 2*r + MMI_w/2 + w_mh/2 + w_mh)
        vias(x0 + MMI_L/2, y0 + 2*r + MMI_w/2 + w_mh/2 + w_mh)


        vias(x0 + MMI_L/2 + tap_ls + w_mh/2 - w_mh, y0 + MMI_w/4 - w + 4*r + 4*w)
        vias(x0 - MMI_L/2 - tap_ls - w_mh/2 + w_mh, y0 + MMI_w/4 - w + 4*r + 4*w)

        shapes(LayermlN).insert(pya.Path([
            pya.Point(x0 + MMI_L/2 + tap_ls + w_mh/2 - 2*w_mh, y0 + 4*r + 6*w),
            pya.Point(x0 - MMI_L/2 - tap_ls - w_mh/2 + 2*w_mh, y0 + 4*r + 6*w)], 4/dbu
        ))

        # Y-Branches

        t = pya.Trans(pya.Trans.R180,
                    x0 + MMI_L/2 + tap_l + yb_l,
                    y0 - yb_w/2 - w/2
        )
        pcell = ly.create_cell("amf_YBranch_TE_1550", "SiEPIC_AMF_Library")
        self.cell.insert(pya.CellInstArray(pcell.cell_index(), t))

        t = pya.Trans(pya.Trans.R0,
                    x0 - MMI_L/2 - tap_l - yb_l,
                    y0 - yb_w/2 - w/2
        )
        pcell = ly.create_cell("amf_YBranch_TE_1550", "SiEPIC_AMF_Library")
        self.cell.insert(pya.CellInstArray(pcell.cell_index(), t))

        # Input waveguide

        shapes(LayerSiN).insert(pya.Box(
            x0 - MMI_L/2 - tap_l - yb_l, y0 - yb_w/2,
            x_start, y0 - yb_w/2 - w
        ))

        # Spiral

        Dy = 30/dbu
        t = pya.Trans(pya.Trans.R90,
            x0 - MMI_L/2 - tap_l + Spiral_Dx,
            y0 - MMI_w/2 - yb_w - Dy,
        )
        pcell = ly.create_cell("Spiral", "EBeam-dev",{
            "length": 200,
            "wg_width": 0.5,
            "min_radius": 5,
            "wg_spacing": 8,
            "spiral_ports": 1,
            "layer": LayerSi
        })
        self.cell.insert(pya.CellInstArray(pcell.cell_index(),t))

        # Horizontal waveguide to match central position of the spiral with connecting arc

        wg = pya.Box(
        x0 - MMI_L/2 - tap_l, y0 - MMI_w/2 - yb_w + 3*w/2,
        x0 - MMI_L/2 - tap_l + Spiral_Dx, y0 - MMI_w/2 - yb_w + 5*w/2
        )
        shapes(LayerSiN).insert(wg)

        # Connecting arc between input y-branch and spiral

        Dy = 58/dbu
        #
        x1 = x0 - MMI_L/2 - tap_l
        y1 = y0 - MMI_w/2 - yb_w - Dy/2 + 2*w

        arcS1 = pya.Polygon(arc_wg_xy(
                x1 + Spiral_Dx,
                y1,
                Dy/2,
                w,
                -90, 90
        ))
        shapes(LayerSiN).insert(arcS1)

        # Connecting waveguides between spiral and output y-branch

        Dy = 66.5/dbu
        x1 = x0 - MMI_L/2 - tap_l
        y1 = y0 - MMI_w/2 - yb_w - Dy/2 + 2*w
        arcS2 = pya.Polygon(arc_wg_xy(
                x1 + Spiral_Dx,
                y1,
                Dy/2,
                w,
                -90, 0
        ))
        shapes(LayerSiN).insert(arcS2)
        Dx1 = (32.9 + 0.85 - Spiral_Dx*dbu)/dbu
        Dy = 33.25/dbu
        coupler_l = MMI_L + 2*tap_l
        Dx2 = coupler_l - Dx1 - 2*Spiral_Dx + w
        arcS3 = pya.Polygon(arc_wg_xy(
                x1 + coupler_l,
                y1 + Dy - Dx2,
                Dx2,
                w,
                90, 0
        ))

        shapes(LayerSiN).insert(arcS3)
        wg = pya.Box(
        x1 + 2*Spiral_Dx + Dx1 - 3*w/2, y1 + Dy - Dx2,
        x1 + 2*Spiral_Dx + Dx1 - w/2, y1
        )
        shapes(LayerSiN).insert(wg)

        # MZI phase tuning heater

        vias(x1 + 2*Spiral_Dx + Dx1 - 3*w/2 + 4.75/dbu, y1 + Dy - Dx2 - w_mh)
        Dy = 66.5/dbu
        Spiral_Dx = 5/dbu
        vias(x1 + Spiral_Dx - w_mh, y1 - Dy/2 - 4.5/dbu)
        shapes(LayermhN).insert(
            pya.Box(x1 + Spiral_Dx, y1 - Dy/2 + w_mh/2,
                x1 + Spiral_Dx - 2*w_mh, y1 - Dy/2 - w_mh/2
            ))
        shapes(LayermhN).insert(
            pya.Polygon(arc_wg_xy(
                x1 + Spiral_Dx,
                y1,
                Dy/2,
                w_mh,
                -90, 0
            ))
        )

        Dx1 = 33.75/dbu - Spiral_Dx
        Dx2 = coupler_l - Dx1 - 2*Spiral_Dx + w
        Dy = 33.25/dbu
        shapes(LayermhN).insert(pya.Box(
            x1 + 2*Spiral_Dx + Dx1 - w - w_mh/2, y1 + Dy - Dx2,
            x1 + 2*Spiral_Dx + Dx1 - w + w_mh/2, y1
        ))

        # Create the pins, as short paths:
        from SiEPIC._globals import PIN_LENGTH as pin_length

        shapes(LayerPinRecN).insert(pya.Path([
            pya.Point(x_start + pin_length/2, y0 - yb_w/2 - w/2),
            pya.Point(x_start - pin_length/2, y0 - yb_w/2 - w/2)
            ], w
        ))
        #
        #

        #
        shapes(LayerPinRecN).insert(pya.Text("opt1", pya.Trans(pya.Trans.R0,
            x_start, y0 - yb_w/2 - w/2))).text_size = 0.5 / dbu
        #
        shapes(LayerPinRecN).insert(pya.Path([
            pya.Point(
                x0 + MMI_L/2 + tap_l + yb_l + pin_length / 2 + 0.2/dbu, y0 - yb_w/2 - w/2
            ),
            pya.Point(
                x0 + MMI_L/2 + tap_l + yb_l - pin_length / 2 + 0.2/dbu, y0 - yb_w/2 - w/2
            )],
        w))
        shapes(LayerSiN).insert(
            pya.Box(
                x0 + MMI_L/2 + tap_l + yb_l + pin_length / 2 + 0.15/dbu, y0 - yb_w/2,
                x0 + MMI_L/2 + tap_l + yb_l + pin_length / 2 - 0.05/dbu, y0 - yb_w/2 - w
            )
        )

        shapes(LayerPinRecN).insert(pya.Text("opt2", pya.Trans(
            pya.Trans.R0,
                x_end, y0 - yb_w/2 - w/2
            ))).text_size = 0.5 / dbu

        # Create the device recognition layer
        shapes(LayerDevRecN).insert(pya.Box(
            x_start, y0 + 4*r + 2*MMI_w + 2*w,
            x_end, y0 - 80/dbu
        ))

class DbRR_MZI_sSpiral(pya.PCellDeclarationHelper):
    """
    The PCell declaration for thermally tunable ring filter.
    """

    def __init__(self):
        super(DbRR_MZI_sSpiral, self).__init__()
        # declare the parameters
        TECHNOLOGY = get_technology_by_name('AMF')
        self.param("silayer", self.TypeLayer, "Si Layer", default=TECHNOLOGY['RIB (10/0@1)'])
        self.param("s", self.TypeShape, "", default=pya.DPoint(0, 0))
        self.param("r", self.TypeDouble, "Radius", default=5)
        self.param("w", self.TypeDouble, "Waveguide Width", default=0.5)
        self.param("MMI_w", self.TypeDouble, "MMI width", default=2)
        self.param("MMI_L", self.TypeDouble, "MMI Length", default=29)
        self.param("MMI_L2", self.TypeDouble, "Secondary MMI Length", default=27)
        self.param("tap_ls", self.TypeDouble, "Taper length", default=10)
        self.param("w_mh", self.TypeInt, "Heater width (nm)", default=3.5)
        self.param("si3layer", self.TypeLayer, "SiEtch2(Rib) Layer", default=TECHNOLOGY['SLAB (12/0@1)'])
        self.param("vllayer", self.TypeLayer, "VL Layer", default=TECHNOLOGY['VIA2 (120/0@1)'])
        self.param("mllayer", self.TypeLayer, "ML Layer", default=TECHNOLOGY['MT2 (125/0@1)'])
        self.param("mhlayer", self.TypeLayer, "MH Layer", default=TECHNOLOGY['HTR (115/0@1)'])
        self.param("textpolygon", self.TypeInt, "Draw text polygon label? 0/1", default=1)
        self.param("textl", self.TypeLayer, "Text Layer", default=TECHNOLOGY['LBL (80/0@1)'])
        self.param("pinrec", self.TypeLayer, "PinRec Layer", default=TECHNOLOGY['PinRec'])
        self.param("devrec", self.TypeLayer, "DevRec Layer", default=TECHNOLOGY['DevRec'])

    def display_text_impl(self):
        # Provide a descriptive text for the cell
        return "Db_RR_MZI_sS"

    def can_create_from_shape_impl(self):
        return False

    def produce_impl(self):
        # This is the main part of the implementation: create the layout
        from math import pi, cos, sin
        from SiEPIC.extend import to_itype

        # fetch the parameters
    #    TECHNOLOGY = get_technology_by_name('GSiP')
        dbu = self.layout.dbu
        ly = self.layout
        shapes = self.cell.shapes

        LayerSi = self.silayer
        LayerSi3 = ly.layer(self.si3layer)
        LayerSiN = ly.layer(LayerSi)
        LayervlN = ly.layer(self.vllayer)
        LayermlN = ly.layer(self.mllayer)
        LayermhN = ly.layer(self.mhlayer)
        TextLayerN = ly.layer(self.textl)
        LayerPinRecN = ly.layer(self.pinrec)
        LayerDevRecN = ly.layer(self.devrec)

        # Define variables for the Modulator
        # Variables for the Si waveguide
        w = to_itype(self.w, dbu)
        r = to_itype(self.r, dbu)

        # Variables for the MH layer
        w_mh = to_itype(self.w_mh, dbu)
        w_mh_min = 2.0/dbu

        # Define Ring centre
        x0 = r + w / 2
        y0 = r + w

        MMI_L = self.MMI_L/dbu
        MMI_w = self.MMI_w/dbu
        yb_l = 15/dbu
        yb_w = 6/dbu
        tap_w = 0.8 / dbu
        tap_ls = self.tap_ls/dbu

        if tap_ls >= 14/dbu:
            tap_l = tap_ls
        else:
            tap_l = 14/dbu

        Spiral_Dx = 5/dbu

        x_start = x0 - MMI_L/2 - tap_l + Spiral_Dx - 25.5/dbu
        x_end = x0 + MMI_L/2 + tap_l + yb_l + 0.2/dbu

        def vias(x_v, y_v):
            sq_s = 3.0/2
            sq_L = 6.0/2
            boxVL3 = pya.Box(x_v - sq_s / dbu, y_v - sq_s / dbu,
                    x_v + sq_s / dbu, y_v + sq_s / dbu)
            boxMH1 = pya.Box(x_v - sq_L / dbu, y_v - sq_L / dbu,
                x_v + sq_L / dbu, y_v + sq_L / dbu)
            shapes(LayervlN).insert(boxVL3)
            shapes(LayermhN).insert(boxMH1)
            shapes(LayermlN).insert(boxMH1)
            shapes(LayerPinRecN).insert(boxMH1)
            shapes(LayerPinRecN).insert(
                pya.Text("elec2h2", pya.Trans(pya.Trans.R0, x_v, y_v))
            ).text_size = 0.5 / dbu

        #####################
        # Generate the layout:
        # MMI 1


        mmi = pya.Box(x0 - MMI_L/2, y0 + MMI_w / 2,
                      x0 + MMI_L/2, y0 - MMI_w / 2)
        shapes(LayerSiN).insert(mmi)

        # Tapers for MMI 1

        taperTL = pya.Polygon([
                pya.Point(x0 - MMI_L/2 - tap_ls, y0 + MMI_w/4 + w/2),
                pya.Point(x0 - MMI_L/2, y0 + MMI_w/4 + tap_w/2),
                pya.Point(x0 - MMI_L/2, y0 + MMI_w/4 - tap_w/2),
                pya.Point(x0 - MMI_L/2 - tap_ls, y0 + MMI_w/4 - w/2),
        ])
        taperBL = pya.Polygon([
                pya.Point(x0 - MMI_L/2 - tap_l, y0 - MMI_w/4 + w/2),
                pya.Point(x0 - MMI_L/2, y0 - MMI_w/4 + tap_w/2),
                pya.Point(x0 - MMI_L/2, y0 - MMI_w/4 - tap_w/2),
                pya.Point(x0 - MMI_L/2 - tap_l, y0 - MMI_w/4 - w/2),
        ])
        taperTR = pya.Polygon([
                pya.Point(x0 + MMI_L/2 + tap_ls, y0 + MMI_w/4 + w/2),
                pya.Point(x0 + MMI_L/2, y0 + MMI_w/4 + tap_w/2),
                pya.Point(x0 + MMI_L/2, y0 + MMI_w/4 - tap_w/2),
                pya.Point(x0 + MMI_L/2 + tap_ls, y0 + MMI_w/4 - w/2),
        ])
        taperBR = pya.Polygon([
                pya.Point(x0 + MMI_L/2 + tap_l, y0 - MMI_w/4 + w/2),
                pya.Point(x0 + MMI_L/2, y0 - MMI_w/4 + tap_w/2),
                pya.Point(x0 + MMI_L/2, y0 - MMI_w/4 - tap_w/2),
                pya.Point(x0 + MMI_L/2 + tap_l, y0 - MMI_w/4 - w/2),
        ])
        shapes(LayerSiN).insert(taperTL)
        shapes(LayerSiN).insert(taperBL)
        shapes(LayerSiN).insert(taperTR)
        shapes(LayerSiN).insert(taperBR)

        from SiEPIC.utils import arc_wg_xy
        # def arc_wg_xy(x, y, r, w, theta_start, theta_stop, DevRec=None):

        # Connecting arcs - MMI 1 to MMI 2

        arcR = pya.Polygon(arc_wg_xy(
                x0 + MMI_L/2 + tap_ls ,
                y0 + self.r/dbu + MMI_w/4,
                self.r / dbu,
                self.w / dbu,
                -90, 90
        ))
        arcL = pya.Polygon(arc_wg_xy(
                x0 - MMI_L/2 - tap_ls ,
                y0 + self.r/dbu + MMI_w/4,
                self.r / dbu,
                self.w / dbu,
                90, -90
        ))
        shapes(LayerSiN).insert(arcR)
        shapes(LayerSiN).insert(arcL)

        # MMI 2, tapers and ring

        x1 = x0
        y1 = y0 + MMI_w/2 + 2*self.r/dbu

        MMI_L2 = to_itype(self.MMI_L2, dbu)

        mmi2 = pya.Box(x1 - MMI_L2/2, y1 + MMI_w / 2,
                      x1 + MMI_L2/2, y1 - MMI_w / 2)
        shapes(LayerSiN).insert(mmi2)

        taperTL2 = pya.Polygon([
                pya.Point(x1 - MMI_L/2 - tap_ls, y1 + MMI_w/4 + w/2),
                pya.Point(x1 - MMI_L2/2, y1 + MMI_w/4 + tap_w/2),
                pya.Point(x1 - MMI_L2/2, y1 + MMI_w/4 - tap_w/2),
                pya.Point(x1 - MMI_L/2 - tap_ls, y1 + MMI_w/4 - w/2),
        ])
        taperBL2 = pya.Polygon([
                pya.Point(x1 - MMI_L/2 - tap_ls, y1 - MMI_w/4 + w/2),
                pya.Point(x1 - MMI_L2/2, y1 - MMI_w/4 + tap_w/2),
                pya.Point(x1 - MMI_L2/2, y1 - MMI_w/4 - tap_w/2),
                pya.Point(x1 - MMI_L/2 - tap_ls, y1 - MMI_w/4 - w/2),
        ])
        taperTR2 = pya.Polygon([
                pya.Point(x1 + MMI_L/2 + tap_ls, y1 + MMI_w/4 + w/2),
                pya.Point(x1 + MMI_L2/2, y1 + MMI_w/4 + tap_w/2),
                pya.Point(x1 + MMI_L2/2, y1 + MMI_w/4 - tap_w/2),
                pya.Point(x1 + MMI_L/2 + tap_ls, y1 + MMI_w/4 - w/2),
        ])
        taperBR2 = pya.Polygon([
                pya.Point(x1 + MMI_L/2 + tap_ls, y1 - MMI_w/4 + w/2),
                pya.Point(x1 + MMI_L2/2, y1 - MMI_w/4 + tap_w/2),
                pya.Point(x1 + MMI_L2/2, y1 - MMI_w/4 - tap_w/2),
                pya.Point(x1 + MMI_L/2 + tap_ls, y1 - MMI_w/4 - w/2),
        ])

        shapes(LayerSiN).insert(taperTL2)
        shapes(LayerSiN).insert(taperBL2)
        shapes(LayerSiN).insert(taperTR2)
        shapes(LayerSiN).insert(taperBR2)

        arcR2 = pya.Polygon(arc_wg_xy(
                x1 + MMI_L/2 + tap_ls ,
                y1 + self.r/dbu + MMI_w/4,
                self.r / dbu,
                self.w / dbu,
                -90, 90
        ))
        arcL2 = pya.Polygon(arc_wg_xy(
                x1 - MMI_L/2 - tap_ls ,
                y1 + self.r/dbu + MMI_w/4,
                self.r / dbu,
                self.w / dbu,
                90, -90
        ))
        shapes(LayerSiN).insert(arcR2)
        shapes(LayerSiN).insert(arcL2)

        wg_T = pya.Box(x1 - MMI_L/2 - tap_ls, y1 + MMI_w/2 + 2*self.r/dbu - self.w/2/dbu,
                      x1 + MMI_L/2 + tap_ls, y1 + MMI_w/2 + 2*self.r/dbu - 3*self.w/2/dbu
        )
        shapes(LayerSiN).insert(wg_T)

        # Heater arcs

        arcR = pya.Polygon(arc_wg_xy(
                x0 + MMI_L/2 + tap_ls + w_mh/2,
                y0 + self.r/dbu + MMI_w/4,
                (self.r - 1) / dbu,
                3 / dbu,
                -90, 90
        ))
        arcL = pya.Polygon(arc_wg_xy(
                x0 - MMI_L/2 - tap_ls - w_mh/2,
                y0 + self.r/dbu + MMI_w/4,
                (self.r - 1) / dbu,
                3 / dbu,
                90, -90
        ))
        shapes(LayermhN).insert(arcR)
        shapes(LayermhN).insert(arcL)
        arcR2 = pya.Polygon(arc_wg_xy(
                x1 + MMI_L/2 + tap_ls + w_mh/2,
                y1 + self.r/dbu + MMI_w/4,
                (self.r - 1) / dbu,
                3 / dbu,
                -90, 90
        ))
        arcL2 = pya.Polygon(arc_wg_xy(
                x1 - MMI_L/2 - tap_ls - w_mh/2,
                y1 + self.r/dbu + MMI_w/4,
                (self.r - 1) / dbu,
                3 / dbu,
                90, -90
        ))
        shapes(LayermhN).insert(arcR2)
        shapes(LayermhN).insert(arcL2)

        # Connecting heater metal between arcs

        shapes(LayermhN).insert(pya.Box(
            x0 - MMI_L/2 - tap_ls - w_mh_min,
            y0 + 2*self.r/dbu + MMI_w/4 - 2.5/dbu,
            x0 - MMI_L/2 - tap_ls - 0/dbu,
            y0 + 2*self.r/dbu + MMI_w/4 + 3.5/dbu,
        ))
        shapes(LayermhN).insert(pya.Box(
            x0 + MMI_L/2 + tap_ls + w_mh_min,
            y0 + 2*self.r/dbu + MMI_w/4 - 2.5/dbu,
            x0 + MMI_L/2 + tap_ls - 0/dbu,
            y0 + 2*self.r/dbu + MMI_w/4 + 3.5/dbu,
        ))

        # Vias for arc arc heaters connection

        vias(x0 + MMI_L/2 + tap_ls + w_mh/2 - w_mh, y0 + MMI_w/4 - w)
        vias(x0 - MMI_L/2 - tap_ls - w_mh/2 + w_mh, y0 + MMI_w/4 - w)

        # Common ground for arc heater

        shapes(LayermlN).insert(pya.Path([
            pya.Point(x0 + MMI_L/2 + tap_ls + w_mh/2 - 2*w_mh, y0),
            pya.Point(x0 - MMI_L/2 - tap_ls - w_mh/2 + 2*w_mh, y0)], 4/dbu
        ))

        # MMI 2 heater

        shapes(LayermhN).insert(
            pya.Box(
                x0 - MMI_L/2, y0 + MMI_w/2 + 2*r + w_mh/2,
                x0 + MMI_L/2, y0 + MMI_w/2 + 2*r - w_mh/2
            )
        )
        # Vias for MMI 2 heater

        vias(x0 - MMI_L/2, y0 + 2*r + MMI_w/2 + w_mh/2 + w_mh)
        vias(x0 + MMI_L/2, y0 + 2*r + MMI_w/2 + w_mh/2 + w_mh)


        vias(x0 + MMI_L/2 + tap_ls + w_mh/2 - w_mh, y0 + MMI_w/4 - w + 4*r + 4*w)
        vias(x0 - MMI_L/2 - tap_ls - w_mh/2 + w_mh, y0 + MMI_w/4 - w + 4*r + 4*w)

        shapes(LayermlN).insert(pya.Path([
            pya.Point(x0 + MMI_L/2 + tap_ls + w_mh/2 - 2*w_mh, y0 + 4*r + 6*w),
            pya.Point(x0 - MMI_L/2 - tap_ls - w_mh/2 + 2*w_mh, y0 + 4*r + 6*w)], 4/dbu
        ))

        # Y-Branches

        t = pya.Trans(pya.Trans.R180,
                    x0 + MMI_L/2 + tap_l + yb_l,
                    y0 - yb_w/2 - w/2
        )
        pcell = ly.create_cell("amf_YBranch_TE_1550", "SiEPIC_AMF_Library")
        self.cell.insert(pya.CellInstArray(pcell.cell_index(), t))

        t = pya.Trans(pya.Trans.R0,
                    x0 - MMI_L/2 - tap_l - yb_l,
                    y0 - yb_w/2 - w/2
        )
        pcell = ly.create_cell("amf_YBranch_TE_1550", "SiEPIC_AMF_Library")
        self.cell.insert(pya.CellInstArray(pcell.cell_index(), t))

        # Input waveguide

        shapes(LayerSiN).insert(pya.Box(
            x0 - MMI_L/2 - tap_l - yb_l, y0 - yb_w/2,
            x_start, y0 - yb_w/2 - w
        ))

        # Spiral

        Dy = 25/dbu
        t = pya.Trans(pya.Trans.R90,
            x0 - MMI_L/2 - tap_l + Spiral_Dx,
            y0 - MMI_w/2 - yb_w - Dy,
        )
        pcell = ly.create_cell("Spiral", "EBeam-dev",{
            "length": 10,
            "wg_width": 0.5,
            "min_radius": 5,
            "wg_spacing": 4,
            "spiral_ports": 1,
            "layer": LayerSi
        })
        self.cell.insert(pya.CellInstArray(pcell.cell_index(),t))

        # Horizontal waveguide to match central position of the spiral with connecting arc

        wg = pya.Box(
            x0 - MMI_L/2 - tap_l, y0 - MMI_w/2 - yb_w + 3*w/2,
            x0 - MMI_L/2 - tap_l + Spiral_Dx, y0 - MMI_w/2 - yb_w + 5*w/2
        )
        shapes(LayerSiN).insert(wg)

        # Connecting arc between input y-branch and spiral

        Dy = 45.0/dbu
        Dx = 2*tap_l + MMI_L - Spiral_Dx
        x1 = x0 - MMI_L/2 - tap_l
        y1 = y0 - MMI_w/2 - yb_w - Dy/2 + 2*w

        arcS1 = pya.Polygon(arc_wg_xy(
                x1 + Spiral_Dx,
                y1,
                Dy/2,
                w,
                -90, 90
        ))
        shapes(LayerSiN).insert(arcS1)

        # Connecting waveguides between spiral and output y-branch
        Dy = 49.5/dbu
        x1 = x0 - MMI_L/2 - tap_l
        y1 = y0 - MMI_w/2 - yb_w - Dy/2 + 2*w
        coupler_l = MMI_L + 2*tap_l
        if Dy > Dx:

            arcS2 = pya.Polygon(arc_wg_xy(
                    x1 + Spiral_Dx,
                    y1,
                    Dy/2,
                    w,
                    -90, 0
            ))
            shapes(LayerSiN).insert(arcS2)
            Dx1 = 33.75/dbu - Spiral_Dx
            Dx2 = coupler_l - Dx1 - 2*Spiral_Dx + w
            arcS3 = pya.Polygon(arc_wg_xy(
                    x1 + coupler_l,
                    y1 + Dy/2 - Dx2,
                    Dx2,
                    w,
                    90, 0
            ))

            shapes(LayerSiN).insert(arcS3)
            wg = pya.Box(
            x1 + 2*Spiral_Dx + Dx1 - 3*w/2, y1 + Dy/2 - Dx2,
            x1 + 2*Spiral_Dx + Dx1 - w/2, y1
            )
            shapes(LayerSiN).insert(wg)

            vias(x1 + 2*Spiral_Dx + Dx1 - 3*w/2 + 4.75/dbu, y1 + Dy - Dx2 - w_mh)
            Dy = 66.5/dbu
            Spiral_Dx = 5/dbu
            vias(x1 + Spiral_Dx - w_mh, y1 - Dy/2 - 4.5/dbu)
            shapes(LayermhN).insert(
                pya.Box(x1 + Spiral_Dx, y1 - Dy/2 + w_mh/2,
                    x1 + Spiral_Dx - 2*w_mh, y1 - Dy/2 - w_mh/2
                ))
            shapes(LayermhN).insert(
                pya.Polygon(arc_wg_xy(
                    x1 + Spiral_Dx,
                    y1,
                    Dy/2,
                    w_mh,
                    -90, 0
                ))
            )

            Dx1 = 33.75/dbu - Spiral_Dx
            Dx2 = coupler_l - Dx1 - 2*Spiral_Dx + w
            Dy = 33.25/dbu
            shapes(LayermhN).insert(pya.Box(
                x1 + 2*Spiral_Dx + Dx1 - w - w_mh/2, y1 + Dy - Dx2,
                x1 + 2*Spiral_Dx + Dx1 - w + w_mh/2, y1
            ))

        if Dx >= Dy:
            wg_l = Dx - Dy
            shapes(LayerSiN).insert(pya.Box(
                x1 + Spiral_Dx, y1 - Dy/2 -w/2,
                x1 + Spiral_Dx + wg_l, y1 - Dy/2 + w/2
            ))
            shapes(LayerSiN).insert(pya.Polygon(arc_wg_xy(
                    x1 + Spiral_Dx + wg_l,
                    y1,
                    Dy/2,
                    w,
                    -90, 0
            )))
            arcS3 = pya.Polygon(arc_wg_xy(
                    x1 + coupler_l,
                    y1,
                    Dy/2,
                    w,
                    90, 0
            ))
            shapes(LayerSiN).insert(arcS3)


            shapes(LayermhN).insert(
                pya.Box(x1 + Spiral_Dx + wg_l, y1 - Dy/2 + w_mh/2,
                    x1 + Spiral_Dx - 2*w_mh, y1 - Dy/2 - w_mh/2
                ))
            vias(x1 + Spiral_Dx - w_mh, y1 - Dy/2 - 4.5/dbu)
            shapes(LayermhN).insert(
                pya.Polygon(arc_wg_xy(
                    x1 + Spiral_Dx + wg_l,
                    y1,
                    Dy/2,
                    w_mh,
                    -90, 0
                ))
            )

            shapes(LayermhN).insert(pya.Box(
                x1 + Spiral_Dx + wg_l + Dy/2 - w_mh/2, y1,
                x1 + Spiral_Dx + wg_l + Dy/2 + w_mh/2, y1 + 2*w_mh
            ))
            vias(x1 + Spiral_Dx + wg_l + Dy/2 + 4.5/dbu, y1 + w_mh)



        # Create the pins, as short paths:
        from SiEPIC._globals import PIN_LENGTH as pin_length

        shapes(LayerPinRecN).insert(pya.Path([
            pya.Point(x_start + pin_length/2, y0 - yb_w/2 - w/2),
            pya.Point(x_start - pin_length/2, y0 - yb_w/2 - w/2)
            ], w
        ))

        shapes(LayerPinRecN).insert(pya.Text("opt1", pya.Trans(pya.Trans.R0,
            x_start, y0 - yb_w/2 - w/2))).text_size = 0.5 / dbu

        shapes(LayerPinRecN).insert(pya.Path([
            pya.Point(
                x0 + MMI_L/2 + tap_l + yb_l + pin_length / 2 + 0.2/dbu, y0 - yb_w/2 - w/2
            ),
            pya.Point(
                x0 + MMI_L/2 + tap_l + yb_l - pin_length / 2 + 0.2/dbu, y0 - yb_w/2 - w/2
            )],
        w))
        shapes(LayerSiN).insert(
            pya.Box(
                x0 + MMI_L/2 + tap_l + yb_l + pin_length / 2 + 0.15/dbu, y0 - yb_w/2,
                x0 + MMI_L/2 + tap_l + yb_l + pin_length / 2 - 0.05/dbu, y0 - yb_w/2 - w
            )
        )

        shapes(LayerPinRecN).insert(pya.Text("opt2", pya.Trans(
            pya.Trans.R0,
                x_end, y0 - yb_w/2 - w/2
            ))).text_size = 0.5 / dbu

        # Create the device recognition layer
        shapes(LayerDevRecN).insert(pya.Box(
            x_start, y0 + 4*r + 2*MMI_w + 2*w,
            x_end, y0 - MMI_w/2 - yb_w - w - Dy - 2*w_mh
        ))

class MZI_isolated_sSpiral(pya.PCellDeclarationHelper):
    """
    The PCell declaration for thermally tunable ring filter.
    """

    def __init__(self):
        super(MZI_isolated_sSpiral, self).__init__()
        # declare the parameters
        TECHNOLOGY = get_technology_by_name('AMF')
        self.param("silayer", self.TypeLayer, "Si Layer", default=TECHNOLOGY['RIB (10/0@1)'])
        self.param("s", self.TypeShape, "", default=pya.DPoint(0, 0))
        self.param("w", self.TypeDouble, "Waveguide Width", default=0.5)
        self.param("MMI_w", self.TypeDouble, "MMI width", default=2)
        self.param("MMI_L", self.TypeDouble, "MMI Length", default=29)
        self.param("tap_ls", self.TypeDouble, "Taper length", default=10)
        self.param("w_mh", self.TypeInt, "Heater width (nm)", default=3.5)
        self.param("si3layer", self.TypeLayer, "SiEtch2(Rib) Layer", default=TECHNOLOGY['SLAB (12/0@1)'])
        self.param("vllayer", self.TypeLayer, "VL Layer", default=TECHNOLOGY['VIA2 (120/0@1)'])
        self.param("mllayer", self.TypeLayer, "ML Layer", default=TECHNOLOGY['MT2 (125/0@1)'])
        self.param("mhlayer", self.TypeLayer, "MH Layer", default=TECHNOLOGY['HTR (115/0@1)'])
        self.param("textpolygon", self.TypeInt, "Draw text polygon label? 0/1", default=1)
        self.param("textl", self.TypeLayer, "Text Layer", default=TECHNOLOGY['LBL (80/0@1)'])
        self.param("pinrec", self.TypeLayer, "PinRec Layer", default=TECHNOLOGY['PinRec'])
        self.param("devrec", self.TypeLayer, "DevRec Layer", default=TECHNOLOGY['DevRec'])

    def display_text_impl(self):
        # Provide a descriptive text for the cell
        return "MZI_isolated_sSpiral"

    def can_create_from_shape_impl(self):
        return False

    def produce_impl(self):
        # This is the main part of the implementation: create the layout
        from math import pi, cos, sin
        from SiEPIC.extend import to_itype
        from SiEPIC.utils import arc_wg_xy

        # fetch the parameters
    #    TECHNOLOGY = get_technology_by_name('GSiP')
        dbu = self.layout.dbu
        ly = self.layout
        shapes = self.cell.shapes

        LayerSi = self.silayer
        LayerSi3 = ly.layer(self.si3layer)
        LayerSiN = ly.layer(LayerSi)
        LayervlN = ly.layer(self.vllayer)
        LayermlN = ly.layer(self.mllayer)
        LayermhN = ly.layer(self.mhlayer)
        TextLayerN = ly.layer(self.textl)
        LayerPinRecN = ly.layer(self.pinrec)
        LayerDevRecN = ly.layer(self.devrec)

        # Define variables for the Modulator
        # Variables for the Si waveguide
        w = to_itype(self.w, dbu)

        # Variables for the MH layer
        w_mh = to_itype(self.w_mh, dbu)

        # Define Ring centre
        x0 = w / 2
        y0 = w

        MMI_L = self.MMI_L/dbu
        MMI_w = self.MMI_w/dbu
        yb_l = 15/dbu
        yb_w = 6/dbu
        tap_w = 0.8 / dbu
        tap_ls = self.tap_ls/dbu

        if tap_ls >= 14/dbu:
            tap_l = tap_ls
        else:
            tap_l = 14/dbu

        Spiral_Dx = 5/dbu

        x_start = x0 - MMI_L/2 - tap_l + Spiral_Dx - 25.5/dbu
        x_end = x0 + MMI_L/2 + tap_l + yb_l + 0.2/dbu

        def vias(x_v, y_v):
            sq_s = 3.0/2
            sq_L = 6.0/2
            boxVL3 = pya.Box(x_v - sq_s / dbu, y_v - sq_s / dbu,
                    x_v + sq_s / dbu, y_v + sq_s / dbu)
            boxMH1 = pya.Box(x_v - sq_L / dbu, y_v - sq_L / dbu,
                x_v + sq_L / dbu, y_v + sq_L / dbu)
            shapes(LayervlN).insert(boxVL3)
            shapes(LayermhN).insert(boxMH1)
            shapes(LayermlN).insert(boxMH1)
            shapes(LayerPinRecN).insert(boxMH1)
            shapes(LayerPinRecN).insert(
                pya.Text("elec2h2", pya.Trans(pya.Trans.R0, x_v, y_v))
            ).text_size = 0.5 / dbu



        # Y-Branches

        t = pya.Trans(pya.Trans.R180,
                    x0 + MMI_L/2 + tap_l + yb_l,
                    y0 - yb_w/2 - w/2
        )
        pcell = ly.create_cell("amf_YBranch_TE_1550", "SiEPIC_AMF_Library")
        self.cell.insert(pya.CellInstArray(pcell.cell_index(), t))

        t = pya.Trans(pya.Trans.R0,
                    x0 - MMI_L/2 - tap_l - yb_l,
                    y0 - yb_w/2 - w/2
        )
        pcell = ly.create_cell("amf_YBranch_TE_1550", "SiEPIC_AMF_Library")
        self.cell.insert(pya.CellInstArray(pcell.cell_index(), t))

        # Input waveguide

        shapes(LayerSiN).insert(pya.Box(
            x0 - MMI_L/2 - tap_l - yb_l, y0 - yb_w/2,
            x_start, y0 - yb_w/2 - w
        ))

        # short MZI Branch

        shapes(LayerSiN).insert(pya.Box(
            x0 - MMI_L/2 - tap_l, y0 - MMI_w/2 + 3*w/2,
            x0 + MMI_L/2 + tap_l, y0 - MMI_w/2 + w/2
        ))

        # Spiral

        Dy = 25/dbu
        t = pya.Trans(pya.Trans.R90,
            x0 - MMI_L/2 - tap_l + Spiral_Dx,
            y0 - MMI_w/2 - yb_w - Dy,
        )
        pcell = ly.create_cell("Spiral", "EBeam-dev",{
            "length": 10,
            "wg_width": 0.5,
            "min_radius": 5,
            "wg_spacing": 4,
            "spiral_ports": 1,
            "layer": LayerSi
        })
        self.cell.insert(pya.CellInstArray(pcell.cell_index(),t))

        # Horizontal waveguide to match central position of the spiral with connecting arc

        wg = pya.Box(
            x0 - MMI_L/2 - tap_l, y0 - MMI_w/2 - yb_w + 3*w/2,
            x0 - MMI_L/2 - tap_l + Spiral_Dx, y0 - MMI_w/2 - yb_w + 5*w/2
        )
        shapes(LayerSiN).insert(wg)

        # Connecting arc between input y-branch and spiral

        Dy = 45.0/dbu
        Dx = 2*tap_l + MMI_L - Spiral_Dx
        x1 = x0 - MMI_L/2 - tap_l
        y1 = y0 - MMI_w/2 - yb_w - Dy/2 + 2*w

        arcS1 = pya.Polygon(arc_wg_xy(
                x1 + Spiral_Dx,
                y1,
                Dy/2,
                w,
                -90, 90
        ))
        shapes(LayerSiN).insert(arcS1)

        # Connecting waveguides between spiral and output y-branch
        Dy = 49.5/dbu
        x1 = x0 - MMI_L/2 - tap_l
        y1 = y0 - MMI_w/2 - yb_w - Dy/2 + 2*w
        coupler_l = MMI_L + 2*tap_l
        if Dy > Dx:

            arcS2 = pya.Polygon(arc_wg_xy(
                    x1 + Spiral_Dx,
                    y1,
                    Dy/2,
                    w,
                    -90, 0
            ))
            shapes(LayerSiN).insert(arcS2)
            Dx1 = 33.75/dbu - Spiral_Dx
            Dx2 = coupler_l - Dx1 - 2*Spiral_Dx + w
            arcS3 = pya.Polygon(arc_wg_xy(
                    x1 + coupler_l,
                    y1 + Dy/2 - Dx2,
                    Dx2,
                    w,
                    90, 0
            ))

            shapes(LayerSiN).insert(arcS3)
            wg = pya.Box(
            x1 + 2*Spiral_Dx + Dx1 - 3*w/2, y1 + Dy/2 - Dx2,
            x1 + 2*Spiral_Dx + Dx1 - w/2, y1
            )
            shapes(LayerSiN).insert(wg)

            vias(x1 + 2*Spiral_Dx + Dx1 - 3*w/2 + 4.75/dbu, y1 + Dy - Dx2 - w_mh)
            Dy = 66.5/dbu
            Spiral_Dx = 5/dbu
            vias(x1 + Spiral_Dx - w_mh, y1 - Dy/2 - 4.5/dbu)
            shapes(LayermhN).insert(
                pya.Box(x1 + Spiral_Dx, y1 - Dy/2 + w_mh/2,
                    x1 + Spiral_Dx - 2*w_mh, y1 - Dy/2 - w_mh/2
                ))
            shapes(LayermhN).insert(
                pya.Polygon(arc_wg_xy(
                    x1 + Spiral_Dx,
                    y1,
                    Dy/2,
                    w_mh,
                    -90, 0
                ))
            )

            Dx1 = 33.75/dbu - Spiral_Dx
            Dx2 = coupler_l - Dx1 - 2*Spiral_Dx + w
            Dy = 33.25/dbu
            shapes(LayermhN).insert(pya.Box(
                x1 + 2*Spiral_Dx + Dx1 - w - w_mh/2, y1 + Dy - Dx2,
                x1 + 2*Spiral_Dx + Dx1 - w + w_mh/2, y1
            ))

        if Dx >= Dy:
            wg_l = Dx - Dy
            shapes(LayerSiN).insert(pya.Box(
                x1 + Spiral_Dx, y1 - Dy/2 -w/2,
                x1 + Spiral_Dx + wg_l, y1 - Dy/2 + w/2
            ))
            shapes(LayerSiN).insert(pya.Polygon(arc_wg_xy(
                    x1 + Spiral_Dx + wg_l,
                    y1,
                    Dy/2,
                    w,
                    -90, 0
            )))
            arcS3 = pya.Polygon(arc_wg_xy(
                    x1 + coupler_l,
                    y1,
                    Dy/2,
                    w,
                    90, 0
            ))
            shapes(LayerSiN).insert(arcS3)


            shapes(LayermhN).insert(
                pya.Box(x1 + Spiral_Dx + wg_l, y1 - Dy/2 + w_mh/2,
                    x1 + Spiral_Dx - 2*w_mh, y1 - Dy/2 - w_mh/2
                ))
            vias(x1 + Spiral_Dx - w_mh, y1 - Dy/2 - 4.5/dbu)
            shapes(LayermhN).insert(
                pya.Polygon(arc_wg_xy(
                    x1 + Spiral_Dx + wg_l,
                    y1,
                    Dy/2,
                    w_mh,
                    -90, 0
                ))
            )

            shapes(LayermhN).insert(pya.Box(
                x1 + Spiral_Dx + wg_l + Dy/2 - w_mh/2, y1,
                x1 + Spiral_Dx + wg_l + Dy/2 + w_mh/2, y1 + 2*w_mh
            ))
            vias(x1 + Spiral_Dx + wg_l + Dy/2 + 4.5/dbu, y1 + w_mh)



        # Create the pins, as short paths:
        from SiEPIC._globals import PIN_LENGTH as pin_length

        shapes(LayerPinRecN).insert(pya.Path([
            pya.Point(x_start + pin_length/2, y0 - yb_w/2 - w/2),
            pya.Point(x_start - pin_length/2, y0 - yb_w/2 - w/2)
            ], w
        ))

        shapes(LayerPinRecN).insert(pya.Text("opt1", pya.Trans(pya.Trans.R0,
            x_start, y0 - yb_w/2 - w/2))).text_size = 0.5 / dbu

        shapes(LayerPinRecN).insert(pya.Path([
            pya.Point(
                x0 + MMI_L/2 + tap_l + yb_l + pin_length / 2 + 0.2/dbu, y0 - yb_w/2 - w/2
            ),
            pya.Point(
                x0 + MMI_L/2 + tap_l + yb_l - pin_length / 2 + 0.2/dbu, y0 - yb_w/2 - w/2
            )],
        w))
        shapes(LayerSiN).insert(
            pya.Box(
                x0 + MMI_L/2 + tap_l + yb_l + pin_length / 2 + 0.15/dbu, y0 - yb_w/2,
                x0 + MMI_L/2 + tap_l + yb_l + pin_length / 2 - 0.05/dbu, y0 - yb_w/2 - w
            )
        )

        shapes(LayerPinRecN).insert(pya.Text("opt2", pya.Trans(
            pya.Trans.R0,
                x_end, y0 - yb_w/2 - w/2
            ))).text_size = 0.5 / dbu

        # Create the device recognition layer
        shapes(LayerDevRecN).insert(pya.Box(
            x_start, y0 + w/2,
            x_end, y0 - MMI_w/2 - yb_w - w - Dy - 2*w_mh
        ))

class MZI_isolated(pya.PCellDeclarationHelper):
    """
    The PCell declaration for thermally tunable ring filter.
    """

    def __init__(self):
        super(MZI_isolated, self).__init__()
        # declare the parameters
        TECHNOLOGY = get_technology_by_name('AMF')
        self.param("silayer", self.TypeLayer, "Si Layer", default=TECHNOLOGY['RIB (10/0@1)'])
        self.param("s", self.TypeShape, "", default=pya.DPoint(0, 0))
        self.param("w", self.TypeDouble, "Waveguide Width", default=0.5)
        self.param("MMI_w", self.TypeDouble, "MMI width", default=2)
        self.param("MMI_L", self.TypeDouble, "MMI Length", default=29)
        self.param("tap_ls", self.TypeDouble, "Taper length", default=10)
        self.param("w_mh", self.TypeInt, "Heater width (nm)", default=3.5)
        self.param("si3layer", self.TypeLayer, "SiEtch2(Rib) Layer", default=TECHNOLOGY['SLAB (12/0@1)'])
        self.param("vllayer", self.TypeLayer, "VL Layer", default=TECHNOLOGY['VIA2 (120/0@1)'])
        self.param("mllayer", self.TypeLayer, "ML Layer", default=TECHNOLOGY['MT2 (125/0@1)'])
        self.param("mhlayer", self.TypeLayer, "MH Layer", default=TECHNOLOGY['HTR (115/0@1)'])
        self.param("textpolygon", self.TypeInt, "Draw text polygon label? 0/1", default=1)
        self.param("textl", self.TypeLayer, "Text Layer", default=TECHNOLOGY['LBL (80/0@1)'])
        self.param("pinrec", self.TypeLayer, "PinRec Layer", default=TECHNOLOGY['PinRec'])
        self.param("devrec", self.TypeLayer, "DevRec Layer", default=TECHNOLOGY['DevRec'])

    def display_text_impl(self):
        # Provide a descriptive text for the cell
        return "MZI_isolated"

    def can_create_from_shape_impl(self):
        return False

    def produce_impl(self):
        # This is the main part of the implementation: create the layout
        from math import pi, cos, sin
        from SiEPIC.extend import to_itype
        from SiEPIC.utils import arc_wg_xy

        # fetch the parameters
    #    TECHNOLOGY = get_technology_by_name('GSiP')
        dbu = self.layout.dbu
        ly = self.layout
        shapes = self.cell.shapes

        LayerSi = self.silayer
        LayerSi3 = ly.layer(self.si3layer)
        LayerSiN = ly.layer(LayerSi)
        LayervlN = ly.layer(self.vllayer)
        LayermlN = ly.layer(self.mllayer)
        LayermhN = ly.layer(self.mhlayer)
        TextLayerN = ly.layer(self.textl)
        LayerPinRecN = ly.layer(self.pinrec)
        LayerDevRecN = ly.layer(self.devrec)

        # Define variables for the Modulator
        # Variables for the Si waveguide
        w = to_itype(self.w, dbu)

        # Variables for the MH layer
        w_mh = to_itype(self.w_mh, dbu)

        # Define Ring centre
        x0 = w / 2
        y0 = w

        MMI_L = self.MMI_L/dbu
        MMI_w = self.MMI_w/dbu
        yb_l = 15/dbu
        yb_w = 6/dbu
        tap_w = 0.8 / dbu
        tap_ls = self.tap_ls/dbu

        if tap_ls >= 14/dbu:
            tap_l = tap_ls
        else:
            tap_l = 14/dbu

        Spiral_Dx = 5/dbu

        x_start = x0 - MMI_L/2 - tap_l + Spiral_Dx - 36.5/dbu
        x_end = x0 + MMI_L/2 + tap_l + yb_l + 0.2/dbu

        def vias(x_v, y_v):
            sq_s = 3.0/2
            sq_L = 6.0/2
            boxVL3 = pya.Box(x_v - sq_s / dbu, y_v - sq_s / dbu,
                    x_v + sq_s / dbu, y_v + sq_s / dbu)
            boxMH1 = pya.Box(x_v - sq_L / dbu, y_v - sq_L / dbu,
                x_v + sq_L / dbu, y_v + sq_L / dbu)
            shapes(LayervlN).insert(boxVL3)
            shapes(LayermhN).insert(boxMH1)
            shapes(LayermlN).insert(boxMH1)
            shapes(LayerPinRecN).insert(boxMH1)
            shapes(LayerPinRecN).insert(
                pya.Text("elec2h2", pya.Trans(pya.Trans.R0, x_v, y_v))
            ).text_size = 0.5 / dbu

        # short MZI Branch

        shapes(LayerSiN).insert(pya.Box(
            x0 - MMI_L/2 - tap_l, y0 - MMI_w/2 + 3*w/2,
            x0 + MMI_L/2 + tap_l, y0 - MMI_w/2 + w/2
        ))

        # Y-Branches

        t = pya.Trans(pya.Trans.R180,
                    x0 + MMI_L/2 + tap_l + yb_l,
                    y0 - yb_w/2 - w/2
        )
        pcell = ly.create_cell("amf_YBranch_TE_1550", "SiEPIC_AMF_Library")
        self.cell.insert(pya.CellInstArray(pcell.cell_index(), t))

        t = pya.Trans(pya.Trans.R0,
                    x0 - MMI_L/2 - tap_l - yb_l,
                    y0 - yb_w/2 - w/2
        )
        pcell = ly.create_cell("amf_YBranch_TE_1550", "SiEPIC_AMF_Library")
        self.cell.insert(pya.CellInstArray(pcell.cell_index(), t))

        # Input waveguide

        shapes(LayerSiN).insert(pya.Box(
            x0 - MMI_L/2 - tap_l - yb_l, y0 - yb_w/2,
            x_start, y0 - yb_w/2 - w
        ))

        # Spiral

        Dy = 30/dbu
        t = pya.Trans(pya.Trans.R90,
            x0 - MMI_L/2 - tap_l + Spiral_Dx,
            y0 - MMI_w/2 - yb_w - Dy,
        )
        pcell = ly.create_cell("Spiral", "EBeam-dev",{
            "length": 200,
            "wg_width": 0.5,
            "min_radius": 5,
            "wg_spacing": 8,
            "spiral_ports": 1,
            "layer": LayerSi
        })
        self.cell.insert(pya.CellInstArray(pcell.cell_index(),t))

        # Horizontal waveguide to match central position of the spiral with connecting arc

        wg = pya.Box(
        x0 - MMI_L/2 - tap_l, y0 - MMI_w/2 - yb_w + 3*w/2,
        x0 - MMI_L/2 - tap_l + Spiral_Dx, y0 - MMI_w/2 - yb_w + 5*w/2
        )
        shapes(LayerSiN).insert(wg)

        # Connecting arc between input y-branch and spiral

        Dy = 58/dbu
        #
        x1 = x0 - MMI_L/2 - tap_l
        y1 = y0 - MMI_w/2 - yb_w - Dy/2 + 2*w

        arcS1 = pya.Polygon(arc_wg_xy(
                x1 + Spiral_Dx,
                y1,
                Dy/2,
                w,
                -90, 90
        ))
        shapes(LayerSiN).insert(arcS1)

        # Connecting waveguides between spiral and output y-branch

        Dy = 66.5/dbu
        x1 = x0 - MMI_L/2 - tap_l
        y1 = y0 - MMI_w/2 - yb_w - Dy/2 + 2*w
        arcS2 = pya.Polygon(arc_wg_xy(
                x1 + Spiral_Dx,
                y1,
                Dy/2,
                w,
                -90, 0
        ))
        shapes(LayerSiN).insert(arcS2)
        Dx1 = (32.9 + 0.85 - Spiral_Dx*dbu)/dbu
        Dy = 33.25/dbu
        coupler_l = MMI_L + 2*tap_l
        Dx2 = coupler_l - Dx1 - 2*Spiral_Dx + w
        arcS3 = pya.Polygon(arc_wg_xy(
                x1 + coupler_l,
                y1 + Dy - Dx2,
                Dx2,
                w,
                90, 0
        ))

        shapes(LayerSiN).insert(arcS3)
        wg = pya.Box(
        x1 + 2*Spiral_Dx + Dx1 - 3*w/2, y1 + Dy - Dx2,
        x1 + 2*Spiral_Dx + Dx1 - w/2, y1
        )
        shapes(LayerSiN).insert(wg)

        # MZI phase tuning heater

        vias(x1 + 2*Spiral_Dx + Dx1 - 3*w/2 + 4.75/dbu, y1 + Dy - Dx2 - w_mh)
        Dy = 66.5/dbu
        Spiral_Dx = 5/dbu
        vias(x1 + Spiral_Dx - w_mh, y1 - Dy/2 - 4.5/dbu)
        shapes(LayermhN).insert(
            pya.Box(x1 + Spiral_Dx, y1 - Dy/2 + w_mh/2,
                x1 + Spiral_Dx - 2*w_mh, y1 - Dy/2 - w_mh/2
            ))
        shapes(LayermhN).insert(
            pya.Polygon(arc_wg_xy(
                x1 + Spiral_Dx,
                y1,
                Dy/2,
                w_mh,
                -90, 0
            ))
        )

        Dx1 = 33.75/dbu - Spiral_Dx
        Dx2 = coupler_l - Dx1 - 2*Spiral_Dx + w
        Dy = 33.25/dbu
        shapes(LayermhN).insert(pya.Box(
            x1 + 2*Spiral_Dx + Dx1 - w - w_mh/2, y1 + Dy - Dx2,
            x1 + 2*Spiral_Dx + Dx1 - w + w_mh/2, y1
        ))

        # Create the pins, as short paths:
        from SiEPIC._globals import PIN_LENGTH as pin_length

        shapes(LayerPinRecN).insert(pya.Path([
            pya.Point(x_start + pin_length/2, y0 - yb_w/2 - w/2),
            pya.Point(x_start - pin_length/2, y0 - yb_w/2 - w/2)
            ], w
        ))

        shapes(LayerPinRecN).insert(pya.Text("opt1", pya.Trans(pya.Trans.R0,
            x_start, y0 - yb_w/2 - w/2))).text_size = 0.5 / dbu

        shapes(LayerPinRecN).insert(pya.Path([
            pya.Point(
                x0 + MMI_L/2 + tap_l + yb_l + pin_length / 2 + 0.2/dbu, y0 - yb_w/2 - w/2
            ),
            pya.Point(
                x0 + MMI_L/2 + tap_l + yb_l - pin_length / 2 + 0.2/dbu, y0 - yb_w/2 - w/2
            )],
        w))
        shapes(LayerSiN).insert(
            pya.Box(
                x0 + MMI_L/2 + tap_l + yb_l + pin_length / 2 + 0.15/dbu, y0 - yb_w/2,
                x0 + MMI_L/2 + tap_l + yb_l + pin_length / 2 - 0.05/dbu, y0 - yb_w/2 - w
            )
        )

        shapes(LayerPinRecN).insert(pya.Text("opt2", pya.Trans(
            pya.Trans.R0,
                x_end, y0 - yb_w/2 - w/2
            ))).text_size = 0.5 / dbu

        # Create the device recognition layer
        shapes(LayerDevRecN).insert(pya.Box(
            x_start, y0 + w/2,
            x_end, y0 - MMI_w/2 - yb_w - w - 2*Dy - 2*w_mh
        ))

class DbRR_Isolated(pya.PCellDeclarationHelper):
    """
    The PCell declaration for thermally tunable ring filter.
    """

    def __init__(self):
        super(DbRR_Isolated, self).__init__()
        # declare the parameters
        TECHNOLOGY = get_technology_by_name('AMF')
        self.param("silayer", self.TypeLayer, "Si Layer", default=TECHNOLOGY['RIB (10/0@1)'])
        self.param("s", self.TypeShape, "", default=pya.DPoint(0, 0))
        self.param("r", self.TypeDouble, "Radius", default=5)
        self.param("w", self.TypeDouble, "Waveguide Width", default=0.5)
        self.param("MMI_w", self.TypeDouble, "MMI width", default=2)
        self.param("MMI_L", self.TypeDouble, "MMI Length", default=29)
        self.param("MMI_L2", self.TypeDouble, "Secondary MMI Length", default=27)
        self.param("tap_ls", self.TypeDouble, "Taper length", default=10)
        self.param("w_mh", self.TypeInt, "Heater width (nm)", default=3.5)
        self.param("si3layer", self.TypeLayer, "SiEtch2(Rib) Layer", default=TECHNOLOGY['SLAB (12/0@1)'])
        self.param("vllayer", self.TypeLayer, "VL Layer", default=TECHNOLOGY['VIA2 (120/0@1)'])
        self.param("mllayer", self.TypeLayer, "ML Layer", default=TECHNOLOGY['MT2 (125/0@1)'])
        self.param("mhlayer", self.TypeLayer, "MH Layer", default=TECHNOLOGY['HTR (115/0@1)'])
        self.param("textpolygon", self.TypeInt, "Draw text polygon label? 0/1", default=1)
        self.param("textl", self.TypeLayer, "Text Layer", default=TECHNOLOGY['LBL (80/0@1)'])
        self.param("pinrec", self.TypeLayer, "PinRec Layer", default=TECHNOLOGY['PinRec'])
        self.param("devrec", self.TypeLayer, "DevRec Layer", default=TECHNOLOGY['DevRec'])

    def display_text_impl(self):
        # Provide a descriptive text for the cell
        return "Db_RR_MZI_sS"

    def can_create_from_shape_impl(self):
        return False

    def produce_impl(self):
        # This is the main part of the implementation: create the layout
        from math import pi, cos, sin
        from SiEPIC.extend import to_itype

        # fetch the parameters
    #    TECHNOLOGY = get_technology_by_name('GSiP')
        dbu = self.layout.dbu
        ly = self.layout
        shapes = self.cell.shapes

        LayerSi = self.silayer
        LayerSi3 = ly.layer(self.si3layer)
        LayerSiN = ly.layer(LayerSi)
        LayervlN = ly.layer(self.vllayer)
        LayermlN = ly.layer(self.mllayer)
        LayermhN = ly.layer(self.mhlayer)
        TextLayerN = ly.layer(self.textl)
        LayerPinRecN = ly.layer(self.pinrec)
        LayerDevRecN = ly.layer(self.devrec)

        # Define variables for the Modulator
        # Variables for the Si waveguide
        w = to_itype(self.w, dbu)
        r = to_itype(self.r, dbu)

        # Variables for the MH layer
        w_mh = to_itype(self.w_mh, dbu)
        w_mh_min = 2.0/dbu

        # Define Ring centre
        x0 = r + w / 2
        y0 = r + w

        MMI_L = self.MMI_L/dbu
        MMI_w = self.MMI_w/dbu
        yb_l = 15/dbu
        yb_w = 6/dbu
        tap_w = 0.8 / dbu
        tap_ls = self.tap_ls/dbu

        if tap_ls >= 14/dbu:
            tap_l = tap_ls
        else:
            tap_l = 14/dbu

        Spiral_Dx = 5/dbu

        x_start = x0 - MMI_L/2 - tap_l - 5.5/dbu
        x_end = x0 + MMI_L/2 + tap_l + 5.5/dbu

        def vias(x_v, y_v):
            sq_s = 3.0/2
            sq_L = 6.0/2
            boxVL3 = pya.Box(x_v - sq_s / dbu, y_v - sq_s / dbu,
                    x_v + sq_s / dbu, y_v + sq_s / dbu)
            boxMH1 = pya.Box(x_v - sq_L / dbu, y_v - sq_L / dbu,
                x_v + sq_L / dbu, y_v + sq_L / dbu)
            shapes(LayervlN).insert(boxVL3)
            shapes(LayermhN).insert(boxMH1)
            shapes(LayermlN).insert(boxMH1)
            shapes(LayerPinRecN).insert(boxMH1)
            shapes(LayerPinRecN).insert(
                pya.Text("elec2h2", pya.Trans(pya.Trans.R0, x_v, y_v))
            ).text_size = 0.5 / dbu

        #####################
        # Generate the layout:
        # MMI 1


        mmi = pya.Box(x0 - MMI_L/2, y0 + MMI_w / 2,
                      x0 + MMI_L/2, y0 - MMI_w / 2)
        shapes(LayerSiN).insert(mmi)



        # Tapers for MMI 1

        taperTL = pya.Polygon([
                pya.Point(x0 - MMI_L/2 - tap_ls, y0 + MMI_w/4 + w/2),
                pya.Point(x0 - MMI_L/2, y0 + MMI_w/4 + tap_w/2),
                pya.Point(x0 - MMI_L/2, y0 + MMI_w/4 - tap_w/2),
                pya.Point(x0 - MMI_L/2 - tap_ls, y0 + MMI_w/4 - w/2),
        ])
        taperBL = pya.Polygon([
                pya.Point(x0 - MMI_L/2 - tap_l, y0 - MMI_w/4 + w/2),
                pya.Point(x0 - MMI_L/2, y0 - MMI_w/4 + tap_w/2),
                pya.Point(x0 - MMI_L/2, y0 - MMI_w/4 - tap_w/2),
                pya.Point(x0 - MMI_L/2 - tap_l, y0 - MMI_w/4 - w/2),
        ])
        taperTR = pya.Polygon([
                pya.Point(x0 + MMI_L/2 + tap_ls, y0 + MMI_w/4 + w/2),
                pya.Point(x0 + MMI_L/2, y0 + MMI_w/4 + tap_w/2),
                pya.Point(x0 + MMI_L/2, y0 + MMI_w/4 - tap_w/2),
                pya.Point(x0 + MMI_L/2 + tap_ls, y0 + MMI_w/4 - w/2),
        ])
        taperBR = pya.Polygon([
                pya.Point(x0 + MMI_L/2 + tap_l, y0 - MMI_w/4 + w/2),
                pya.Point(x0 + MMI_L/2, y0 - MMI_w/4 + tap_w/2),
                pya.Point(x0 + MMI_L/2, y0 - MMI_w/4 - tap_w/2),
                pya.Point(x0 + MMI_L/2 + tap_l, y0 - MMI_w/4 - w/2),
        ])
        shapes(LayerSiN).insert(taperTL)
        shapes(LayerSiN).insert(taperBL)
        shapes(LayerSiN).insert(taperTR)
        shapes(LayerSiN).insert(taperBR)

        # Input waveguide

        shapes(LayerSiN).insert(pya.Box(
            x0 - MMI_L/2 - tap_l, y0 - MMI_w/4 + w/2,
            x_start, y0 - MMI_w/4 - w/2
        ))

        # Output waveguide

        shapes(LayerSiN).insert(pya.Box(
            x0 + MMI_L/2 + tap_l, y0 - MMI_w/4 + w/2,
            x_end, y0 - MMI_w/4 - w/2
        ))

        from SiEPIC.utils import arc_wg_xy
        # def arc_wg_xy(x, y, r, w, theta_start, theta_stop, DevRec=None):

        # Connecting arcs - MMI 1 to MMI 2

        arcR = pya.Polygon(arc_wg_xy(
                x0 + MMI_L/2 + tap_ls ,
                y0 + self.r/dbu + MMI_w/4,
                self.r / dbu,
                self.w / dbu,
                -90, 90
        ))
        arcL = pya.Polygon(arc_wg_xy(
                x0 - MMI_L/2 - tap_ls ,
                y0 + self.r/dbu + MMI_w/4,
                self.r / dbu,
                self.w / dbu,
                90, -90
        ))
        shapes(LayerSiN).insert(arcR)
        shapes(LayerSiN).insert(arcL)

        # MMI 2, tapers and ring

        x1 = x0
        y1 = y0 + MMI_w/2 + 2*self.r/dbu

        MMI_L2 = to_itype(self.MMI_L2, dbu)

        mmi2 = pya.Box(x1 - MMI_L2/2, y1 + MMI_w / 2,
                      x1 + MMI_L2/2, y1 - MMI_w / 2)
        shapes(LayerSiN).insert(mmi2)

        taperTL2 = pya.Polygon([
                pya.Point(x1 - MMI_L/2 - tap_ls, y1 + MMI_w/4 + w/2),
                pya.Point(x1 - MMI_L2/2, y1 + MMI_w/4 + tap_w/2),
                pya.Point(x1 - MMI_L2/2, y1 + MMI_w/4 - tap_w/2),
                pya.Point(x1 - MMI_L/2 - tap_ls, y1 + MMI_w/4 - w/2),
        ])
        taperBL2 = pya.Polygon([
                pya.Point(x1 - MMI_L/2 - tap_ls, y1 - MMI_w/4 + w/2),
                pya.Point(x1 - MMI_L2/2, y1 - MMI_w/4 + tap_w/2),
                pya.Point(x1 - MMI_L2/2, y1 - MMI_w/4 - tap_w/2),
                pya.Point(x1 - MMI_L/2 - tap_ls, y1 - MMI_w/4 - w/2),
        ])
        taperTR2 = pya.Polygon([
                pya.Point(x1 + MMI_L/2 + tap_ls, y1 + MMI_w/4 + w/2),
                pya.Point(x1 + MMI_L2/2, y1 + MMI_w/4 + tap_w/2),
                pya.Point(x1 + MMI_L2/2, y1 + MMI_w/4 - tap_w/2),
                pya.Point(x1 + MMI_L/2 + tap_ls, y1 + MMI_w/4 - w/2),
        ])
        taperBR2 = pya.Polygon([
                pya.Point(x1 + MMI_L/2 + tap_ls, y1 - MMI_w/4 + w/2),
                pya.Point(x1 + MMI_L2/2, y1 - MMI_w/4 + tap_w/2),
                pya.Point(x1 + MMI_L2/2, y1 - MMI_w/4 - tap_w/2),
                pya.Point(x1 + MMI_L/2 + tap_ls, y1 - MMI_w/4 - w/2),
        ])

        shapes(LayerSiN).insert(taperTL2)
        shapes(LayerSiN).insert(taperBL2)
        shapes(LayerSiN).insert(taperTR2)
        shapes(LayerSiN).insert(taperBR2)

        arcR2 = pya.Polygon(arc_wg_xy(
                x1 + MMI_L/2 + tap_ls ,
                y1 + self.r/dbu + MMI_w/4,
                self.r / dbu,
                self.w / dbu,
                -90, 90
        ))
        arcL2 = pya.Polygon(arc_wg_xy(
                x1 - MMI_L/2 - tap_ls ,
                y1 + self.r/dbu + MMI_w/4,
                self.r / dbu,
                self.w / dbu,
                90, -90
        ))
        shapes(LayerSiN).insert(arcR2)
        shapes(LayerSiN).insert(arcL2)

        wg_T = pya.Box(x1 - MMI_L/2 - tap_ls, y1 + MMI_w/2 + 2*self.r/dbu - self.w/2/dbu,
                      x1 + MMI_L/2 + tap_ls, y1 + MMI_w/2 + 2*self.r/dbu - 3*self.w/2/dbu
        )
        shapes(LayerSiN).insert(wg_T)

        # Heater arcs

        arcR = pya.Polygon(arc_wg_xy(
                x0 + MMI_L/2 + tap_ls + w_mh/2,
                y0 + self.r/dbu + MMI_w/4,
                (self.r - 1) / dbu,
                3 / dbu,
                -90, 90
        ))
        arcL = pya.Polygon(arc_wg_xy(
                x0 - MMI_L/2 - tap_ls - w_mh/2,
                y0 + self.r/dbu + MMI_w/4,
                (self.r - 1) / dbu,
                3 / dbu,
                90, -90
        ))
        shapes(LayermhN).insert(arcR)
        shapes(LayermhN).insert(arcL)
        arcR2 = pya.Polygon(arc_wg_xy(
                x1 + MMI_L/2 + tap_ls + w_mh/2,
                y1 + self.r/dbu + MMI_w/4,
                (self.r - 1) / dbu,
                3 / dbu,
                -90, 90
        ))
        arcL2 = pya.Polygon(arc_wg_xy(
                x1 - MMI_L/2 - tap_ls - w_mh/2,
                y1 + self.r/dbu + MMI_w/4,
                (self.r - 1) / dbu,
                3 / dbu,
                90, -90
        ))
        shapes(LayermhN).insert(arcR2)
        shapes(LayermhN).insert(arcL2)

        # Connecting heater metal between arcs

        shapes(LayermhN).insert(pya.Box(
            x0 - MMI_L/2 - tap_ls - w_mh_min,
            y0 + 2*self.r/dbu + MMI_w/4 - 2.5/dbu,
            x0 - MMI_L/2 - tap_ls - 0/dbu,
            y0 + 2*self.r/dbu + MMI_w/4 + 3.5/dbu,
        ))
        shapes(LayermhN).insert(pya.Box(
            x0 + MMI_L/2 + tap_ls + w_mh_min,
            y0 + 2*self.r/dbu + MMI_w/4 - 2.5/dbu,
            x0 + MMI_L/2 + tap_ls - 0/dbu,
            y0 + 2*self.r/dbu + MMI_w/4 + 3.5/dbu,
        ))

        # Vias for arc arc heaters connection

        vias(x0 + MMI_L/2 + tap_ls + w_mh/2 - w_mh, y0 + MMI_w/4 - w)
        vias(x0 - MMI_L/2 - tap_ls - w_mh/2 + w_mh, y0 + MMI_w/4 - w)

        # Common ground for arc heater

        shapes(LayermlN).insert(pya.Path([
            pya.Point(x0 + MMI_L/2 + tap_ls + w_mh/2 - 2*w_mh, y0),
            pya.Point(x0 - MMI_L/2 - tap_ls - w_mh/2 + 2*w_mh, y0)], 4/dbu
        ))

        # MMI 2 heater

        shapes(LayermhN).insert(
            pya.Box(
                x0 - MMI_L/2, y0 + MMI_w/2 + 2*r + w_mh/2,
                x0 + MMI_L/2, y0 + MMI_w/2 + 2*r - w_mh/2
            )
        )
        # Vias for MMI 2 heater

        vias(x0 - MMI_L/2, y0 + 2*r + MMI_w/2 + w_mh/2 + w_mh)
        vias(x0 + MMI_L/2, y0 + 2*r + MMI_w/2 + w_mh/2 + w_mh)


        vias(x0 + MMI_L/2 + tap_ls + w_mh/2 - w_mh, y0 + MMI_w/4 - w + 4*r + 4*w)
        vias(x0 - MMI_L/2 - tap_ls - w_mh/2 + w_mh, y0 + MMI_w/4 - w + 4*r + 4*w)

        shapes(LayermlN).insert(pya.Path([
            pya.Point(x0 + MMI_L/2 + tap_ls + w_mh/2 - 2*w_mh, y0 + 4*r + 6*w),
            pya.Point(x0 - MMI_L/2 - tap_ls - w_mh/2 + 2*w_mh, y0 + 4*r + 6*w)], 4/dbu
        ))

        # Create the pins, as short paths:
        from SiEPIC._globals import PIN_LENGTH as pin_length

        shapes(LayerPinRecN).insert(pya.Path([
            pya.Point(x_start + pin_length/2, y0 - w),
            pya.Point(x_start - pin_length/2, y0 - w)
            ], w
        ))

        shapes(LayerPinRecN).insert(pya.Text("opt1", pya.Trans(pya.Trans.R0,
            x_start, y0 - w))).text_size = 0.5 / dbu

        shapes(LayerPinRecN).insert(pya.Path([
            pya.Point(
                x_end - pin_length/2, y0 - w
            ),
            pya.Point(
                x_end + pin_length/2, y0 - w
            )],
        w))

        shapes(LayerPinRecN).insert(pya.Text("opt2", pya.Trans(
            pya.Trans.R0,
                x_end, y0 - w
            ))).text_size = 0.5 / dbu

        # Create the device recognition layer
        shapes(LayerDevRecN).insert(pya.Box(
            x_start, y0 + 4*r + 2*MMI_w + 2*w,
            x_end, y0 - MMI_w/2 - w - 2*w_mh
        ))

class RR_Isolated(pya.PCellDeclarationHelper):
    """
    The PCell declaration for thermally tunable ring filter.
    """

    def __init__(self):
        super(RR_Isolated, self).__init__()
        # declare the parameters
        TECHNOLOGY = get_technology_by_name('AMF')
        self.param("silayer", self.TypeLayer, "Si Layer", default=TECHNOLOGY['RIB (10/0@1)'])
        self.param("s", self.TypeShape, "", default=pya.DPoint(0, 0))
        self.param("r", self.TypeDouble, "Radius", default=5)
        self.param("w", self.TypeDouble, "Waveguide Width", default=0.5)
        self.param("MMI_w", self.TypeDouble, "MMI width", default=2)
        self.param("MMI_L", self.TypeDouble, "MMI Length", default=29)
        self.param("MMI_L2", self.TypeDouble, "Secondary MMI Length", default=27)
        self.param("tap_ls", self.TypeDouble, "Taper length", default=10)
        self.param("w_mh", self.TypeInt, "Heater width (nm)", default=3.5)
        self.param("si3layer", self.TypeLayer, "SiEtch2(Rib) Layer", default=TECHNOLOGY['SLAB (12/0@1)'])
        self.param("vllayer", self.TypeLayer, "VL Layer", default=TECHNOLOGY['VIA2 (120/0@1)'])
        self.param("mllayer", self.TypeLayer, "ML Layer", default=TECHNOLOGY['MT2 (125/0@1)'])
        self.param("mhlayer", self.TypeLayer, "MH Layer", default=TECHNOLOGY['HTR (115/0@1)'])
        self.param("textpolygon", self.TypeInt, "Draw text polygon label? 0/1", default=1)
        self.param("textl", self.TypeLayer, "Text Layer", default=TECHNOLOGY['LBL (80/0@1)'])
        self.param("pinrec", self.TypeLayer, "PinRec Layer", default=TECHNOLOGY['PinRec'])
        self.param("devrec", self.TypeLayer, "DevRec Layer", default=TECHNOLOGY['DevRec'])

    def display_text_impl(self):
        # Provide a descriptive text for the cell
        return "Db_RR_MZI_sS"

    def can_create_from_shape_impl(self):
        return False

    def produce_impl(self):
        # This is the main part of the implementation: create the layout
        from math import pi, cos, sin
        from SiEPIC.extend import to_itype

        # fetch the parameters
    #    TECHNOLOGY = get_technology_by_name('GSiP')
        dbu = self.layout.dbu
        ly = self.layout
        shapes = self.cell.shapes

        LayerSi = self.silayer
        LayerSi3 = ly.layer(self.si3layer)
        LayerSiN = ly.layer(LayerSi)
        LayervlN = ly.layer(self.vllayer)
        LayermlN = ly.layer(self.mllayer)
        LayermhN = ly.layer(self.mhlayer)
        TextLayerN = ly.layer(self.textl)
        LayerPinRecN = ly.layer(self.pinrec)
        LayerDevRecN = ly.layer(self.devrec)

        # Define variables for the Modulator
        # Variables for the Si waveguide
        w = to_itype(self.w, dbu)
        r = to_itype(self.r, dbu)

        # Variables for the MH layer
        w_mh = to_itype(self.w_mh, dbu)

        # Define Ring centre
        x0 = r + w / 2
        y0 = r + w

        MMI_L = self.MMI_L/dbu
        MMI_w = self.MMI_w/dbu
        yb_l = 15/dbu
        yb_w = 6/dbu
        tap_w = 0.8 / dbu
        tap_ls = self.tap_ls/dbu

        if tap_ls >= 14/dbu:
            tap_l = tap_ls
        else:
            tap_l = 14/dbu

        Spiral_Dx = 5/dbu

        x_start = x0 - MMI_L/2 - tap_l - 5.5/dbu
        x_end = x0 + MMI_L/2 + tap_l + 5.5/dbu

        def vias(x_v, y_v):
            sq_s = 3.0/2
            sq_L = 6.0/2
            boxVL3 = pya.Box(x_v - sq_s / dbu, y_v - sq_s / dbu,
                    x_v + sq_s / dbu, y_v + sq_s / dbu)
            boxMH1 = pya.Box(x_v - sq_L / dbu, y_v - sq_L / dbu,
                x_v + sq_L / dbu, y_v + sq_L / dbu)
            shapes(LayervlN).insert(boxVL3)
            shapes(LayermhN).insert(boxMH1)
            shapes(LayermlN).insert(boxMH1)
            shapes(LayerPinRecN).insert(boxMH1)
            shapes(LayerPinRecN).insert(
                pya.Text("elec2h2", pya.Trans(pya.Trans.R0, x_v, y_v))
            ).text_size = 0.5 / dbu

        #####################
        # Generate the layout:
        # MMI 1


        mmi = pya.Box(x0 - MMI_L/2, y0 + MMI_w / 2,
                      x0 + MMI_L/2, y0 - MMI_w / 2)
        shapes(LayerSiN).insert(mmi)



        # Tapers for MMI 1

        taperTL = pya.Polygon([
                pya.Point(x0 - MMI_L/2 - tap_ls, y0 + MMI_w/4 + w/2),
                pya.Point(x0 - MMI_L/2, y0 + MMI_w/4 + tap_w/2),
                pya.Point(x0 - MMI_L/2, y0 + MMI_w/4 - tap_w/2),
                pya.Point(x0 - MMI_L/2 - tap_ls, y0 + MMI_w/4 - w/2),
        ])
        taperBL = pya.Polygon([
                pya.Point(x0 - MMI_L/2 - tap_l, y0 - MMI_w/4 + w/2),
                pya.Point(x0 - MMI_L/2, y0 - MMI_w/4 + tap_w/2),
                pya.Point(x0 - MMI_L/2, y0 - MMI_w/4 - tap_w/2),
                pya.Point(x0 - MMI_L/2 - tap_l, y0 - MMI_w/4 - w/2),
        ])
        taperTR = pya.Polygon([
                pya.Point(x0 + MMI_L/2 + tap_ls, y0 + MMI_w/4 + w/2),
                pya.Point(x0 + MMI_L/2, y0 + MMI_w/4 + tap_w/2),
                pya.Point(x0 + MMI_L/2, y0 + MMI_w/4 - tap_w/2),
                pya.Point(x0 + MMI_L/2 + tap_ls, y0 + MMI_w/4 - w/2),
        ])
        taperBR = pya.Polygon([
                pya.Point(x0 + MMI_L/2 + tap_l, y0 - MMI_w/4 + w/2),
                pya.Point(x0 + MMI_L/2, y0 - MMI_w/4 + tap_w/2),
                pya.Point(x0 + MMI_L/2, y0 - MMI_w/4 - tap_w/2),
                pya.Point(x0 + MMI_L/2 + tap_l, y0 - MMI_w/4 - w/2),
        ])
        shapes(LayerSiN).insert(taperTL)
        shapes(LayerSiN).insert(taperBL)
        shapes(LayerSiN).insert(taperTR)
        shapes(LayerSiN).insert(taperBR)

        # Input waveguide

        shapes(LayerSiN).insert(pya.Box(
            x0 - MMI_L/2 - tap_l, y0 - MMI_w/4 + w/2,
            x_start, y0 - MMI_w/4 - w/2
        ))

        # Output waveguide

        shapes(LayerSiN).insert(pya.Box(
            x0 + MMI_L/2 + tap_l, y0 - MMI_w/4 + w/2,
            x_end, y0 - MMI_w/4 - w/2
        ))

        # Ring top waveguide
        shapes(LayerSiN).insert(pya.Box(
            x0 - MMI_L/2 - tap_ls, y0 + MMI_w/4 + 2*r + w/2,
            x0 + MMI_L/2 + tap_ls, y0 + MMI_w/4 + 2*r - w/2,
        ))

        from SiEPIC.utils import arc_wg_xy
        # def arc_wg_xy(x, y, r, w, theta_start, theta_stop, DevRec=None):

        # Connecting arcs - MMI 1 to MMI 2

        arcR = pya.Polygon(arc_wg_xy(
                x0 + MMI_L/2 + tap_ls ,
                y0 + self.r/dbu + MMI_w/4,
                self.r / dbu,
                self.w / dbu,
                -90, 90
        ))
        arcL = pya.Polygon(arc_wg_xy(
                x0 - MMI_L/2 - tap_ls ,
                y0 + self.r/dbu + MMI_w/4,
                self.r / dbu,
                self.w / dbu,
                90, -90
        ))
        shapes(LayerSiN).insert(arcR)
        shapes(LayerSiN).insert(arcL)

        arcR = pya.Polygon(arc_wg_xy(
                x0 + MMI_L/2 + tap_ls + w_mh/2,
                y0 + self.r/dbu + MMI_w/4,
                (self.r - 1) / dbu,
                3 / dbu,
                -90, 90
        ))
        arcL = pya.Polygon(arc_wg_xy(
                x0 - MMI_L/2 - tap_ls - w_mh/2,
                y0 + self.r/dbu + MMI_w/4,
                (self.r - 1) / dbu,
                3 / dbu,
                90, -90
        ))
        shapes(LayermhN).insert(arcR)
        shapes(LayermhN).insert(arcL)

        # Vias for arc arc heaters connection

        vias(x0 + MMI_L/2 + tap_ls + w_mh/2 - w_mh, y0 + MMI_w/4 - w)
        vias(x0 - MMI_L/2 - tap_ls - w_mh/2 + w_mh, y0 + MMI_w/4 - w)

        # Common ground for arc heater

        shapes(LayermlN).insert(pya.Path([
            pya.Point(x0 + MMI_L/2 + tap_ls + w_mh/2 - 2*w_mh, y0),
            pya.Point(x0 - MMI_L/2 - tap_ls - w_mh/2 + 2*w_mh, y0)], 4/dbu
        ))

        vias(x0 + MMI_L/2 + tap_ls + w_mh/2 - w_mh, y0 + MMI_w/4 + 2*r)
        vias(x0 - MMI_L/2 - tap_ls - w_mh/2 + w_mh, y0 + MMI_w/4 + 2*r)

        # Common ground for arc heater

        shapes(LayermlN).insert(pya.Path([
            pya.Point(x0 + MMI_L/2 + tap_ls + w_mh/2 - 2*w_mh, y0 + MMI_w/4 + 2*r),
            pya.Point(x0 - MMI_L/2 - tap_ls - w_mh/2 + 2*w_mh, y0 + MMI_w/4 + 2*r)], 4/dbu
        ))


class Bruno_AMF_Library(pya.Library):
  """
  The library where we will put the PCell into
  """

  def __init__(self):

    # Set the description
    self.description = "Bruno_AMF_Library"

    # Create the PCell declarations

    self.layout().register_pcell("Double_RR_MZI", Db_MMI_RR())
    self.layout().register_pcell("Double_RR_MZI_smallerSpiral", DbRR_MZI_sSpiral())
    self.layout().register_pcell("MZI_isolated_sSpiral",MZI_isolated_sSpiral())
    self.layout().register_pcell("MZI_isolated",MZI_isolated())
    self.layout().register_pcell("Double_RR_Isolated", DbRR_Isolated())
    self.layout().register_pcell("RR_Isolated", RR_Isolated())
    # That would be the place to put in more PCells ...

    # Register us with the name "MyLib".
    # If a library with that name already existed, it will be replaced then.
    self.register("Bruno_AMF_Library")


# Instantiate and register the library
Bruno_AMF_Library()
