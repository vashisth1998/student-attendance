import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Attendance Tracker", layout="centered")
st.title("Attendance Tracker App 📊")
st.write("Apni Master Excel file aur Daily CSV files upload karein aur total attendance nikalein.")

st.subheader("1. Upload Master Data")
master_file = st.file_uploader("Master Excel File upload karein (xlsx/csv)", type=['xlsx', 'csv'])

st.subheader("2. Upload Daily Attendance")
daily_files = st.file_uploader("Daily CSV files upload karein", type=['csv'], accept_multiple_files=True)

if st.button("Calculate Attendance"):
    if master_file is not None and len(daily_files) > 0:
        try:
            # File reading
            if master_file.name.endswith('.csv'):
                master_df = pd.read_csv(master_file)
            else:
                master_df = pd.read_excel(master_file)
            
            if 'Total Attendance' not in master_df.columns:
                master_df['Total Attendance'] = 0
            else:
                master_df['Total Attendance'] = 0 

            all_unmatched_names = []

            for file in daily_files:
                daily_df = pd.read_csv(file)
                col_name = None
                for col in daily_df.columns:
                    if 'name' in col.lower() or 'participant' in col.lower():
                        col_name = col
                        break
                
                if col_name:
                    daily_df[col_name] = daily_df[col_name].fillna("")
                    raw_names = daily_df[col_name].astype(str).str.strip().tolist()
                    
                    matched_in_this_file = set()
                    cleaned_to_raw_map = {}
                    
                    # SUPER CLEANING: Sirf alphabets aur numbers rakhenge
                    # Matalab '1-Anirudh-004' ban jayega '1anirudh004'
                    for raw in raw_names:
                        if raw:
                            clean_name = re.sub(r'[^a-z0-9]', '', str(raw).lower())
                            cleaned_to_raw_map[clean_name] = raw
                    
                    for index, row in master_df.iterrows():
                        name = str(row.get('Student Name', '')).replace('nan', '').strip().lower()
                        p_id = str(row.get('pariticipant_id', '')).replace('nan', '').strip().lower() 
                        
                        last_3 = p_id[-3:] if len(p_id) >= 3 else p_id
                        name_parts = name.split()
                        first_name = name_parts[0] if name_parts else name
                        first_4 = first_name[:4] if len(first_name) >= 4 else first_name
                        name_no_space = name.replace(" ", "")

                        student_matched = False
                        
                        for clean_name in cleaned_to_raw_map.keys():
                            # LOGIC 1: Agar string mein 3-digit ID present hai
                            if last_3 in clean_name:
                                # Name cross-verification (First name ya 4 letters hone chahiye taaki kisi aur ka ID na match ho jaye)
                                if first_name in clean_name or first_4 in clean_name:
                                    student_matched = True
                                else:
                                    # Agar first name nahi, toh last/middle name se verify karein
                                    for part in name_parts:
                                        if len(part) >= 3 and part in clean_name:
                                            student_matched = True
                                            break
                            
                            # LOGIC 2: Bina ID wale bache (Sirf naam daala hai)
                            if not student_matched:
                                if clean_name == name_no_space or clean_name == first_name:
                                    student_matched = True
                                    
                            if student_matched:
                                matched_in_this_file.add(clean_name)
                                break # Bacha mil gaya, aage search band karein
                                
                        if student_matched:
                            master_df.at[index, 'Total Attendance'] += 1
                            
                    # Find unmatched names to show warning
                    for clean_name, raw_name in cleaned_to_raw_map.items():
                        if clean_name not in matched_in_this_file:
                            all_unmatched_names.append(raw_name)
                            
                else:
                    st.warning(f"File {file.name} mein 'Name' wala koi column nahi mila.")

            st.success("Attendance successfully calculate ho gayi hai! 🎉")
            
            total_students = len(master_df)
            present_today = (master_df['Total Attendance'] > 0).sum()
            
            st.metric(label="🟢 Today Total Present Students", value=f"{present_today} / {total_students}")
            
            if all_unmatched_names:
                st.warning("⚠️ Neeche diye gaye naam Master list se match nahi hue (Yeh teacher ho sakte hain ya typo ho sakta hai):")
                st.write(list(set(all_unmatched_names))) 

            st.dataframe(master_df) 

            csv = master_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download Final Report",
                data=csv,
                file_name='Final_Attendance_Report.csv',
                mime='text/csv',
            )
            
        except Exception as e:
            st.error(f"Koi error aayi hai. Error details: {e}")
    else:
        st.warning("Pehle Master Excel file aur kam se kam ek Daily CSV file upload karein!")
