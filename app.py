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
                            clean_letters = re.sub(r'[^a-z]', '', str(raw).lower())
                            nums_in_raw = [int(x) for x in re.findall(r'\d+', str(raw))]
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
                        
                        try:
                            target_id_int = int(last_3_str)
                        except:
                            target_id_int = -1
                            
                        name_parts = name.split()
                        clean_name_parts = [re.sub(r'[^a-z]', '', p) for p in name_parts]
                        valid_parts = [p for p in clean_name_parts if len(p) >= 3]
                        if not valid_parts:
                            valid_parts = clean_name_parts
                        
                        clean_first_name = valid_parts[0] if valid_parts else ""
                        name_no_space = re.sub(r'[^a-z]', '', name)

                        student_present_today = False
                        
                        # Har bache ko daily records mein dhoondhna
                        for record in daily_records:
                            student_matched = False
                            has_id_match = False
                            
                            # CONDITION 1: Check ID presence
                            if last_3_str and last_3_str in record['clean_all']:
                                has_id_match = True
                            elif target_id_int != -1:
                                for n in record['nums']:
                                    # Agar bache ne poori ID 26055 bhi likhi hogi, toh % 1000 usko 55 pakad lega
                                    if n == target_id_int or n % 1000 == target_id_int or n % 10000 == target_id_int:
                                        has_id_match = True
                                        break
                            
                            # CONDITION 2: Cross-verify Name if ID matched
                            if has_id_match:
                                name_verified = False
                                for part in valid_parts:
                                    if len(part) >= 3:
                                        if part[:3] in record['letters']:
                                            name_verified = True
                                            break
                                    else:
                                        if part in record['letters']:
                                            name_verified = True
                                            break
                                if name_verified:
                                    student_matched = True
                                    
                            # CONDITION 3: Bina ID ke bache (Jinhone sirf naam likha hai)
                            if not student_matched and clean_first_name:
                                if record['letters'] == name_no_space:
                                    student_matched = True
                                elif record['letters'] == clean_first_name:
                                    student_matched = True
                                elif record['letters'].startswith(clean_first_name) and len(record['letters']) >= len(clean_first_name):
                                    student_matched = True
                                elif record['letters'] in valid_parts:
                                    student_matched = True
                                    
                            if student_matched:
                                matched_in_this_file.add(record['raw'])
                                student_present_today = True # Bache ki entry mil gayi
                                
                        # Loop ke baad: Agar bacha kisi bhi naam se present tha, toh 1 attendance badhao
                        if student_present_today:
                            master_df.at[index, 'Total Attendance'] += 1
                                
                    # End of file: Jo bach gaye, sirf unhe unmatched mein dalo
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
