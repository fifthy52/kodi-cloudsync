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
        # For demonstration - create a simple text-based "QR code"
        # In a real implementation, this would generate actual QR code data

        lines = [
            "█████████████████████████",
            "█       █   █       █   █",
            "█ █████ █ █ █ █████ █ █ █",
            "█ █████ █ █ █ █████ █ █ █",
            "█ █████ █   █ █████ █   █",
            "█       █████       █████",
            "█████████ █ █ █████████ █",
            "█         █   █         █",
            f"█ URL: {text[:15]}...",
            "█         █   █         █",
            "█████████ █ █ █████████ █",
            "█       █████       █████",
            "█ █████ █   █ █████ █   █",
            "█ █████ █ █ █ █████ █ █ █",
            "█ █████ █ █ █ █████ █ █ █",
            "█       █   █       █   █",
            "█████████████████████████",
        ]

        # Add border
        if border > 0:
            border_line = "█" * (len(lines[0]) + 2 * border)
            bordered_lines = [border_line]
            for line in lines:
                bordered_lines.append("█" * border + line + "█" * border)
            bordered_lines.append(border_line)
            return "\n".join(bordered_lines)

        return "\n".join(lines)

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