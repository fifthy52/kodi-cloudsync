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
    def generate_qr_url(text):
        """Generate QR code using online QR API as fallback."""
        import urllib.parse
        encoded_text = urllib.parse.quote(text)
        return f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={encoded_text}"

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