from PIL import Image, ImageDraw, ImageFont

BORDER = (136, 126, 203)      # C64 light blue border
BACKGROUND = (64, 49, 141)    # C64 blue screen
FOREGROUND = (136, 126, 203)
LINES = ("**** COMMODORE 64 BASIC V2 ****", "",
         "64K RAM SYSTEM  38911 BASIC BYTES FREE", "", "READY.")


class C64Screen:
    """Draws the C64 start-up screen, used when no game is selected."""

    @staticmethod
    def _font(size):
        for name in ("Menlo.ttc", "Courier New Bold.ttf", "couri.ttf", "DejaVuSansMono-Bold.ttf",
                     "Courier New.ttf"):
            try:
                return ImageFont.truetype(name, size)
            except OSError:
                continue
        return ImageFont.load_default(size=size)

    @classmethod
    def render(cls, size):
        """Return an RGB image of exactly `size` (width, height)."""
        w, h = size
        img = Image.new("RGB", size, BORDER)
        draw = ImageDraw.Draw(img)
        bx, by = int(w * 0.1), int(h * 0.1)
        draw.rectangle((bx, by, w - bx, h - by), fill=BACKGROUND)
        font = cls._font(max(8, int((w - 2 * bx) / 42 * 1.6)))
        line_h = font.getbbox("Mg")[3] * 1.35
        x, y = bx + int(w * 0.02), by + int(h * 0.04)
        for i, line in enumerate(LINES):
            draw.text((x, y + i * line_h), line, font=font, fill=FOREGROUND)
        cy = y + len(LINES) * line_h - line_h * 0.9
        draw.rectangle((x, cy, x + line_h * 0.6, cy + line_h * 0.9), fill=FOREGROUND)
        return img
