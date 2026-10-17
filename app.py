import streamlit as st
from PIL import Image
from intelhex import IntelHex
import io

st.set_page_config(page_title="IconEdit Pro", page_icon="⚡", layout="centered")

st.title("⚡ Fast IconEdit CLI-to-Web Tool")
st.write("Upload exactly **250x80** image to generate `.hex` and `.sym` files.")

FIXED_WIDTH = 250
FIXED_HEIGHT = 80
FLASH_START_ADDRESS = 0x08004000  

uploaded_file = st.file_uploader("Drag & Drop or Browse Image", type=["png", "jpg", "jpeg", "bmp"])

if uploaded_file is not None:
    img = Image.open(uploaded_file)
    width, height = img.size
    
    if width != FIXED_WIDTH or height != FIXED_HEIGHT:
        st.error(f"❌ Error: Image size is {width}x{height}. It must be exactly {FIXED_WIDTH}x{FIXED_HEIGHT}!")
    else:
        st.success("✅ Image size validated (250x80). Processing...")
        
        img = img.convert('RGB')
        
        raw_binary_data = bytearray()
        for y in range(FIXED_HEIGHT):
            for x in range(FIXED_WIDTH):
                r, g, b = img.getpixel((x, y))
                rgb565 = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
                raw_binary_data.append((rgb565 >> 8) & 0xFF)
                raw_binary_data.append(rgb565 & 0xFF)
        
        total_bytes = len(raw_binary_data)
        
        ih = IntelHex()
        ih.frombytes(raw_binary_data, offset=FLASH_START_ADDRESS)
        
        hex_buffer = io.StringIO()
        ih.write_hex_file(hex_buffer)
        hex_string = hex_buffer.getvalue()
        
        sym_string = (
            f"// IconEdit Auto-Generated Symbol File\n"
            f"// Address Space: Flash Memory\n"
            f"// --------------------------------------------------\n"
            f"SYMBOL_NAME          : COMPANY_LOGO_ICON\n"
            f"START_ADDRESS        : {hex(FLASH_START_ADDRESS)}\n"
            f"END_ADDRESS          : {hex(FLASH_START_ADDRESS + total_bytes - 1)}\n"
            f"SIZE_BYTES           : {total_bytes} Bytes\n"
            f"DIMENSIONS           : {FIXED_WIDTH}x{FIXED_HEIGHT} Pixels (RGB565)\n"
        )
        
        st.markdown("### 📥 Download Output Files")
        col1, col2 = st.columns(2)
        
        with col1:
            st.download_button(
                label="Download .hex File",
                data=hex_string,
                file_name="logo_250x80.hex",
                mime="text/plain"
            )
            
        with col2:
            st.download_button(
                label="Download .sym File",
                data=sym_string,
                file_name="logo_250x80.sym",
                mime="text/plain"
            )
            
        st.info(f"Metadata Info: Logo size in memory is {total_bytes} bytes starting at {hex(FLASH_START_ADDRESS)}.")
