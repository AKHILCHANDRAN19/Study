import os
import glob
import fitz  # PyMuPDF

def parse_text_to_styled_html(raw_text, filename):
    """
    Parses the raw text and wraps it in styling tags. 
    PyMuPDF's Story engine will natively render this into the PDF.
    """
    lines = raw_text.split('\n')
    
    html = f"""
    <div style="font-family: helvetica, sans-serif; color: #333333; line-height: 1.5;">
        <h1 style="color: #4a90e2; text-align: center; border-bottom: 2px solid #4a90e2; padding-bottom: 10px;">
            {filename}
        </h1>
    """
    
    in_logic = False
    
    for line in lines:
        line = line.strip()
        if not line:
            html += "<br>"
            continue
            
        # Style "Question X"
        if line.lower().startswith('question'):
            html += f'<h2 style="color: #2b6cb0; margin-top: 20px;">{line}</h2>'
            
        # Style "Translation / Core Text"
        elif line.lower().startswith('translation:'):
            html += f'<p style="font-size: 12pt; font-weight: bold; color: #2d3748;">{line}</p>'
            
        # Style "Options" block
        elif line.lower().startswith('options:'):
            html += f'<div style="background-color: #ebf8ff; padding: 10px; border-left: 4px solid #4299e1; color: #2c5282; margin-bottom: 10px;"><b>{line}</b></div>'
            
        # Style "Logical Elimination" header
        elif line.lower().startswith('logical elimination:'):
            html += f'<h3 style="color: #d97706; margin-top: 15px; margin-bottom: 5px;">💡 {line}</h3>'
            in_logic = True
            
        # Style "Answer" block
        elif line.lower().startswith('answer:'):
            html += f'<div style="background-color: #f0fff4; padding: 10px; border: 1px solid #9ae6b4; color: #276749; font-weight: bold; text-align: center; margin-top: 10px;">✅ {line}</div><hr style="color: #eeeeee; margin-top: 20px;">'
            in_logic = False
            
        # Standard text
        else:
            if in_logic:
                html += f'<p style="color: #555555; margin-left: 15px; margin-top: 2px; margin-bottom: 2px;">{line}</p>'
            else:
                html += f'<p style="color: #444444; margin-top: 2px; margin-bottom: 2px;">{line}</p>'
                
    html += '</div>'
    return html


def convert_txt_to_beautiful_pdf():
    # Define folder paths
    quiz_folder = "/storage/emulated/0/quiz"
    output_folder = os.path.join(quiz_folder, "Beautiful_PDFs")
    
    # Check if the quiz folder exists
    if not os.path.exists(quiz_folder):
        print(f"❌ Error: Could not find the folder: {quiz_folder}")
        return
        
    # Create the output subfolder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"📁 Created subfolder: {output_folder}")
        
    # Scrape all .txt files
    search_pattern = os.path.join(quiz_folder, "*.txt")
    txt_files = glob.glob(search_pattern)
    
    if not txt_files:
        print(f"⚠️ No .txt files found in {quiz_folder}")
        return
        
    print(f"🔍 Found {len(txt_files)} text file(s). Starting PDF conversion...\n")
    
    for txt_path in txt_files:
        filename = os.path.basename(txt_path)
        pdf_filename = filename.replace(".txt", ".pdf")
        pdf_path = os.path.join(output_folder, pdf_filename)
        
        print(f"⏳ Converting: {filename} -> {pdf_filename}")
        
        # Read the text file
        with open(txt_path, "r", encoding="utf-8") as f:
            raw_text = f.read()
            
        # Parse into styled format
        styled_html = parse_text_to_styled_html(raw_text, filename.replace(".txt", ""))
        
        try:
            # 1. Initialize the Story with our styled HTML
            story = fitz.Story(html=styled_html)
            
            # 2. Use DocumentWriter (The correct method for modern PyMuPDF)
            writer = fitz.DocumentWriter(pdf_path)
            
            # A4 page dimensions
            page_rect = fitz.Rect(0, 0, 595, 842)
            # Writeable area (Leaves 40 points of margin on all sides)
            content_rect = fitz.Rect(40, 40, 555, 802)
            
            more = 1
            while more:
                # Begin a new page and get its rendering device
                dev = writer.begin_page(page_rect)
                
                # Place the content inside the writeable margins
                more, _ = story.place(content_rect)
                
                # Draw the story to the device
                story.draw(dev)
                
                # End the page
                writer.end_page()
                
            # Close and save the file
            writer.close()
            
        except Exception as e:
            print(f"❌ Error during PDF generation for {filename}: {e}")
            return
            
    print("\n✅ All done! Your beautiful PDFs are saved in:")
    print(output_folder)

# Run the converter
if __name__ == "__main__":
    convert_txt_to_beautiful_pdf()
