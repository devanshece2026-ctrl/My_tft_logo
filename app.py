import streamlit as st
from PIL import Image
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
                # RGB888 to RGB565 conversion
                rgb565 = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
                raw_binary_data.append((rgb565 >> 8) & 0xFF)
                raw_binary_data.append(rgb565 & 0xFF)
        
        total_bytes = len(raw_binary_data)
        
        # --- Intel HEX Format Manual Generation (No intelhex library needed) ---
        hex_lines = []
        current_address = FLASH_START_ADDRESS
        
        # 16 बाइट्स के टुकड़ों में बाइनरी डेटा को Intel HEX रिकॉर्ड में बदलना
        for i in range(0, total_bytes, 16):
            chunk = raw_binary_data[i:i+16]
            byte_count = len(chunk)
            
            # अगर एड्रेस 16-bit लिमिट (64KB) से ऊपर है, तो Extended Linear Address Record (04) जोड़ें
            if i == 0 or (current_address & 0xFFFF) == 0:
                high_word = (current_address >> 16) & 0xFFFF
                ext_rec = f":02000004{high_word:04X}"
                # Checksum कैलकुलेशन
                ext_cs = (0x02 + 0x00 + 0x00 + 0x04 + ((high_word >> 8) & 0xFF) + (high_word & 0xFF)) & 0xFF
                ext_cs = (-ext_cs) & 0xFF
                hex_lines.append(f"{ext_rec}{ext_cs:02X}")
            
            low_address = current_address & 0xFFFF
            record_type = 0x00  # Data Record
            
            # हेक्स लाइन का ढांचा बनाना
            line_str = f"{byte_count:02X}{low_address:04X}{record_type:02X}"
            line_str += "".join(f"{b:02X}" for b in chunk)
            
            # Checksum कैलकुलेट करना
            checksum = byte_count + ((low_address >> 8) & 0xFF) + (low_address & 0xFF) + record_type
            checksum += sum(chunk)
            checksum = (-checksum) & 0xFF
            
            hex_lines.append(f":{line_str}{checksum:02X}")
            current_address += byte_count
            
        # End of File Record जोड़ना
        hex_lines.append(":00000001FF")
        hex_string = "\n".join(hex_lines) + "\n"
        
        # --- SYM फ़ाइल जनरेशन ---
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
