import numpy as np

class CS_FOV:
    def __init__(self, canvas, pt):
        self.canvas = canvas
        self.dc = canvas.dc if hasattr(canvas, 'dc') else canvas.get_draw_classes()
        self.pt_ctr = pt
        self.scale_x = 1.0  # degrees per pixel
        self.scale_y = 1.0
        self.pa_rot_deg = 0.0
        self.flip_tf = False

    def set_scale(self, scale_x, scale_y):
        self.scale_x = scale_x
        self.scale_y = scale_y

    def set_pos(self, pt):
        self.pt_ctr = pt

    def set_pa(self, pa_deg):
        self.pa_rot_deg = pa_deg

    def flip_x(self, obj, xcenter):
        for o in obj.objects:
            if hasattr(o, 'flip_x'):
                o.flip_x(xcenter)

    def remove(self):
        if hasattr(self, 'moircs_box') and self.moircs_box:
            try:
                self.canvas.delete_object(self.moircs_box)
            except Exception as e:
                print(f"Error removing moircs_box: {e}")
        self.moircs_box = None


class MOIRCS_FOV(CS_FOV):
    def __init__(self, canvas, pt):
        super().__init__(canvas, pt)
        self.moircs_fov = (0.0666667, 0.116667)  # 4x7 arcmin in degrees
        self.text_off = 1.0
        self.moircs_box = None
        self._build()

    def _build(self):
        x, y = self.pt_ctr
        # Compute radius in pixels
        xr = self.moircs_fov[0] * 0.5 / self.scale_x if self.scale_x > 0 else 10.0
        yr = self.moircs_fov[1] * 0.5 / self.scale_y if self.scale_y > 0 else 10.0
        dc = self.dc
        pixel_offset = 280.0  # Fixed offset in pixels

        # Detector polygons
        det2 = dc.Polygon(
            np.array([(x - xr, y), (x + xr, y), (x + xr, y + yr), (x - xr, y + yr)], dtype=float),
            color='yellow', linewidth=1
        )
        det1 = dc.Polygon(
            np.array([(x - xr, y), (x + xr, y), (x + xr, y - yr), (x - xr, y - yr)], dtype=float),
            color='yellow', linewidth=1
        )

        # Labels
        fov_label = dc.Text(
            x - xr, y + yr, text="MOIRCS FOV (4x7 arcmin)", color='white', bgcolor='black', bgalpha=1.0
        )
        label1 = dc.Text(
            x + xr, y - (yr * self.text_off), text='Det 1', color='white', bgcolor='black', bgalpha=1.0
        )
        label2 = dc.Text(
            x + xr, y + (yr * self.text_off), text='Det 2', color='white', bgcolor='black', bgalpha=1.0
        )

        # FOV circle
        radius_deg = 3.0 / 60.0  # 3 arcmin
        radius_pixels = radius_deg / self.scale_x if self.scale_x > 0 else 10.0
        fov_circle = dc.Circle(x, y, radius_pixels, color='white', linewidth=1, fill=False)

        # Dashed lines
        edge_line_ch1 = dc.Line(
            x - xr, y - pixel_offset, x + xr, y - pixel_offset, color='yellow', linewidth=1, linestyle='dash'
        )
        edge_line_ch2 = dc.Line(
            x - xr, y + pixel_offset, x + xr, y + pixel_offset, color='yellow', linewidth=1, linestyle='dash'
        )

        # Create compound object
        self.moircs_box = dc.CompoundObject(
            fov_circle, det2, det1, fov_label, label1, label2, edge_line_ch1, edge_line_ch2
        )
        self.canvas.add(self.moircs_box)

    def __update(self):
        if not self.moircs_box:
            print("FOV overlay has been removed; skipping update.")
            return

        x, y = self.pt_ctr[:2]
        # Compute radius in pixels
        xr = self.moircs_fov[0] * 0.5 / self.scale_x if self.scale_x > 0 else 10.0
        yr = self.moircs_fov[1] * 0.5 / self.scale_y if self.scale_y > 0 else 10.0
        pixel_offset = 280.0

        # Update objects
        self.moircs_box.objects[0].x = x
        self.moircs_box.objects[0].y = y
        radius_deg = 3.0 / 60.0
        self.moircs_box.objects[0].radius = radius_deg / self.scale_x if self.scale_x > 0 else 10.0
        self.moircs_box.objects[1].points = np.array(
            [(x - xr, y), (x + xr, y), (x + xr, y + yr), (x - xr, y + yr)], dtype=float
        )  # Det 2
        self.moircs_box.objects[2].points = np.array(
            [(x - xr, y), (x + xr, y), (x + xr, y - yr), (x - xr, y - yr)], dtype=float
        )  # Det 1
        self.moircs_box.objects[3].x, self.moircs_box.objects[3].y = x - xr, y + yr  # FOV label
        self.moircs_box.objects[4].x, self.moircs_box.objects[4].y = x + xr, y - (yr * self.text_off)  # Label 1
        self.moircs_box.objects[5].x, self.moircs_box.objects[5].y = x + xr, y + (yr * self.text_off)  # Label 2
        self.moircs_box.objects[3].rot_deg = self.moircs_box.objects[4].rot_deg = self.moircs_box.objects[5].rot_deg = self.pa_rot_deg
        self.moircs_box.objects[6].x1, self.moircs_box.objects[6].y1 = x - xr, y - pixel_offset  # CH1 line
        self.moircs_box.objects[6].x2, self.moircs_box.objects[6].y2 = x + xr, y - pixel_offset
        self.moircs_box.objects[7].x1, self.moircs_box.objects[7].y1 = x - xr, y + pixel_offset  # CH2 line
        self.moircs_box.objects[7].x2, self.moircs_box.objects[7].y2 = x + xr, y + pixel_offset

        print(f"Updated CH1 line: ({x - xr:.2f}, {y - pixel_offset:.2f}) to ({x + xr:.2f}, {y - pixel_offset:.2f})")
        print(f"Updated CH2 line: ({x - xr:.2f}, {y + pixel_offset:.2f}) to ({x + xr:.2f}, {y + pixel_offset:.2f})")

        if self.flip_tf:
            self.flip_x(self.moircs_box, x)
        if self.pa_rot_deg != 0:
            self.moircs_box.rotate_deg([self.pa_rot_deg], [x, y])

    def set_scale(self, scale_x, scale_y):
        super().set_scale(scale_x, scale_y)
        self.__update()

    def set_pos(self, pt):
        super().set_pos(pt)
        self.__update()

    def set_pa(self, pa_deg):
        super().set_pa(pa_deg)
        self.__update()

    def scale_to_image(self, img_width, img_height):
        if img_width <= 0 or img_height <= 0:
            print(f"Invalid image dimensions: width={img_width}, height={img_height}")
            return
        fov_width_deg = self.moircs_fov[0]
        fov_height_deg = self.moircs_fov[1]
        scale_x = fov_width_deg / img_width if img_width > 0 else 1.0
        scale_y = fov_height_deg / img_height if img_height > 0 else 1.0
        self.set_scale(scale_x, scale_y)
        print(f"Scaled to image: width={img_width}, height={img_height}, scale_x={scale_x:.6f}, scale_y={scale_y:.6f}")

    def rebuild(self):
        self.remove()
        self._build()
        self.__update()

