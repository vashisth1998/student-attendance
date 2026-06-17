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
                    daily_records = []
                    
                    # NAYA LOGIC: Naam aur numbers ko bilkul alag-alag todna
                    for raw in raw_names:
                        if raw:
                            # Sirf letters (typo check ke liye)
                            clean_letters = re.sub(r'[^a-z]', '', str(raw).lower())
                            # Sirf numbers ki list (mathematical check ke liye e.g., '009' becomes 9)
                            nums_in_raw = [int(x) for x in re.findall(r'\d+', str(raw))]
                            # Pure clean text (fallback ke liye)
                            clean_all = re.sub(r'[^a-z0-9]', '', str(raw).lower())
                            
                            daily_records.append({
                                'raw': raw,
                                'letters': clean_letters,
                                'nums': nums_in_raw,
                                'clean_all': clean_all
                            })
                    
                    for index, row in master_df.iterrows():
                        name = str(row.get('Student Name', '')).replace('nan', '').strip().lower()
                        p_id = str(row.get('pariticipant_id', '')).replace('nan', '').strip().lower() 
                        
                        last_3_str = p_id[-3:] if len(p_id) >= 3 else p_id
                        
                        # Master ID ke last 3 digits ko number mein convert karna (e.g., '055' -> 55)
                        try:
                            target_id_int = int(last_3_str)
                        except:
                            target_id_int = -1
                            
                        name_parts = name.split()
                        first_name = name_parts[0] if name_parts else name
                        first_3 = first_name[:3] if len(first_name) >= 3 else first_name
                        name_no_space = name.replace(" ", "")

                        student_matched = False
                        
                        for record in daily_records:
                            # CONDITION 1: Exact Number Match (Agar bache ne 55 ya 055 kuch bhi likha ho)
                            if target_id_int != -1 and target_id_int in record['nums']:
                                # Cross verify: Kya naam ke pehle 3 letters match ho rahe hain?
                                if first_3 in record['letters']:
                                    student_matched = True
                                else:
                                    # Agar first name nahi, toh last name check karein
                                    for part in name_parts:
                                        if len(part) >= 3 and part[:3] in record['letters']:
                                            student_matched = True
                                            break
                            
                            # CONDITION 2: Bina ID ke bache (Jinhone sirf naam likha hai)
                            if not student_matched:
                                if record['letters'] == name_no_space or record['letters'] == first_name:
                                    student_matched = True
                                elif last_3_str in record['clean_all'] and first_3 in record['clean_all']:
                                    student_matched = True
                                    
                            if student_matched:
                                matched_in_this_file.add(record['raw'])
                                master_df.at[index, 'Total Attendance'] += 1
                                break
                                
                    # Unmatched check
                    for record in daily_records:
                        if record['raw'] not in matched_in_this_file:
                            all_unmatched_names.append(record['raw'])
                            
                else:
                    st.warning(f"File {file.name} mein 'Name' wala koi column nahi mila.")

            st.success("Attendance successfully calculate ho gayi hai! 🎉")
            
            total_students = len(master_df)
            present_today = (master_df['Total Attendance'] > 0).sum()
            
            st.metric(label="🟢 Today Total Present Students", value=f"{present_today} / {total_students}")
            
            if all_unmatched_names:
                st.warning("⚠️ Neeche diye gaye naam Master list se match nahi hue:")
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
