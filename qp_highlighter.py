import fitz  # PyMuPDF
import re
import os

def highlight_answers(input_pdf, output_pdf):
    # Answer key strictly extracted for Question Booklet Alpha Code: A
    ans_key_A = {
        1: "D", 2: "B", 3: "C", 4: "D", 5: "A", 6: "D", 7: "A", 8: "C", 9: "A", 10: "C",
        11: "C", 12: "C", 13: "D", 14: "D", 15: "B", 16: "B", 17: "D", 18: "C", 19: "D", 20: "B",
        21: "B", 22: "C", 23: "B", 24: "B", 25: "A", 26: "D", 27: "A", 28: "C", 29: "B", 30: "D",
        31: "C", 32: "B", 33: "D", 34: "B", 35: "C", 36: "D", 37: "C", 38: "B", 39: "A", 40: "D",
        41: "D", 42: "B", 43: "A", 44: "D", 45: "A", 46: "B", 47: "A", 48: "A", 49: "C", 50: "A",
        51: "D", 52: "B", 53: "B", 54: "A", 55: "A", 56: "B", 57: "B", 58: "D", 59: "A", 60: "D",
        61: "D", 62: "D", 63: "A", 64: "B", 65: "A", 66: "C", 67: "A", 68: "A", 69: "A", 70: "B",
        71: "C", 72: "D", 73: "A", 74: "A", 75: "A", 76: "C", 77: "A", 78: "B", 79: "D", 80: "A",
        81: "C", 82: "C", 83: "B", 84: "D", 85: "B", 86: "C", 87: "B", 88: "A", 89: "D", 90: "C",
        91: "A", 92: "C", 93: "C", 94: "B", 95: "D", 96: "D", 97: "B", 98: "C", 99: "C", 100: "B"
    }

    print(f"Opening PDF: {input_pdf}")
    if not os.path.exists(input_pdf):
        print("Error: Could not find the file at the specified path.")
        return

    doc = fitz.open(input_pdf)
    
    expected_q = 1
    current_q = 0
    highlighted_questions = set()

    for page_idx in range(len(doc)):
        # Skip the first two pages (instructions)
        if page_idx < 2:
            continue
            
        page = doc[page_idx]
        words = page.get_text("words")
        
        for i, w in enumerate(words):
            text = w[4].strip()
            rect = fitz.Rect(w[:4])
            
            # The FIX: (?!\d) ensures the dot is not followed by another digit (prevents 34.6 from triggering as Question 34)
            match = re.match(r"^(\d+)\.(?!\d)", text)
            if match:
                q_num = int(match.group(1))
                if expected_q <= q_num <= expected_q + 5:
                    if rect.x0 < 200:
                        current_q = q_num
                        expected_q = q_num + 1

            if 1 <= current_q <= 100:
                if text in["A)", "B)", "C)", "D)"]:
                    opt = text[0]
                    
                    if opt == ans_key_A[current_q] and current_q not in highlighted_questions:
                        
                        hl_rect = rect
                        for j in range(i + 1, len(words)):
                            next_w = words[j]
                            next_text = next_w[4].strip()
                            next_rect = fitz.Rect(next_w[:4])
                            
                            if abs(next_rect.y0 - rect.y0) > 10:
                                break
                            if next_text in ["A)", "B)", "C)", "D)"]:
                                break
                                
                            hl_rect = hl_rect | next_rect
                        
                        hl = page.add_highlight_annot(hl_rect)
                        hl.set_colors(stroke=(1, 1, 0)) 
                        hl.update()
                        
                        highlighted_questions.add(current_q)
                        
    doc.save(output_pdf)
    doc.close()
    
    print("\n--- Summary ---")
    print(f"Highlighting complete. Saved to: {output_pdf}")
    print(f"Total questions successfully highlighted: {len(highlighted_questions)}/100")
    
    missing = set(range(1, 101)) - highlighted_questions
    if missing:
        print(f"Missed highlighting for questions: {sorted(missing)}")

# Setup paths
input_path = "/storage/emulated/0/Download/1.pdf"
output_path = "/storage/emulated/0/Download/1_highlighted.pdf"

highlight_answers(input_path, output_path)
