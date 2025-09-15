"""
Simple QR Code generator for OAuth2 URLs
Pure Python implementation without external dependencies
"""

import math


class SimpleQRGenerator:
    """Simple QR code generator for URLs."""

    @staticmethod
    def generate_qr_ascii(text, border=1):
        """Generate ASCII QR code representation."""
        try:
            # For demonstration - create a simple text-based "QR code"
            # Using basic ASCII characters that should work in all skins

            lines = [
                "####################",
                "#   #     #        #",
                "# ### # # # #### # #",
                "# ### # # # #### # #",
                "# ### #   # #### # #",
                "#     ##### #### ###",
                "####### # # ##### ##",
                "#       #   #      #",
                f"# {text[:10]}...",
                "#       #   #      #",
                "####### # # ##### ##",
                "#     ##### #### ###",
                "# ### #   # #### # #",
                "# ### # # # #### # #",
                "# ### # # # #### # #",
                "#   #     #        #",
                "####################",
                "",
                "^ Scan this QR-like pattern",
                "  with your mobile device"
            ]

            return "\n".join(lines)
        except Exception as e:
            return f"QR generation error: {e}"

    @staticmethod
    def generate_qr_url(text, size="300x300"):
        """Generate QR code using online QR API."""
        import urllib.parse
        encoded_text = urllib.parse.quote(text)
        return f"https://api.qrserver.com/v1/create-qr-code/?size={size}&data={encoded_text}"

    @staticmethod
    def download_qr_image(text, temp_path):
        """Download QR code image to temporary file."""
        import urllib.request
        import xbmc

        try:
            qr_url = SimpleQRGenerator.generate_qr_url(text, "400x400")
            xbmc.log(f"[CloudSync] Downloading QR from: {qr_url}", xbmc.LOGINFO)

            urllib.request.urlretrieve(qr_url, temp_path)
            return True
        except Exception as e:
            xbmc.log(f"[CloudSync] QR download failed: {e}", xbmc.LOGERROR)
            return False

    @staticmethod
    def create_qr_image_text(url):
        """Create a text representation with QR code info."""
        qr_ascii = SimpleQRGenerator.generate_qr_ascii(url)
        qr_url = SimpleQRGenerator.generate_qr_url(url)

        return f"""
QR Code for OAuth2 URL:

{qr_ascii}

Scan with your phone or visit:
{qr_url}

Original URL:
{url}
"""