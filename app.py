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
                    
                    # RECORD PREPARATION
                    for raw in raw_names:
                        if raw:
                            clean_letters = re.sub(r'[^a-z]', '', str(raw).lower())
                            numbers_in_raw_str = re.findall(r'\d+', str(raw))
                            nums_in_raw = [int(x) for x in numbers_in_raw_str]
                            last_num = int(numbers_in_raw_str[-1]) if numbers_in_raw_str else -1
                            
                            daily_records.append({
                                'raw': raw,
                                'letters': clean_letters,
                                'nums': nums_in_raw,
                                'last_num': last_num
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
                        valid_parts = [p for p in clean_name_parts if len(p) >= 2]
                        clean_full_name = re.sub(r'[^a-z]', '', name)
                        first_name = valid_parts[0] if valid_parts else ""

                        student_present_today = False
                        
                        for record in daily_records:
                            student_matched = False
                            d_letters = record['letters']
                            d_nums = record['nums']
                            
                            # RULE 1: STRICT LAST DIGIT MATCH
                            if target_id_int != -1 and record['last_num'] == target_id_int:
                                student_matched = True
                                
                            # RULE 2: AGGRESSIVE NAME MATCH
                            if not student_matched and clean_full_name:
                                if clean_full_name in d_letters:
                                    student_matched = True
                                elif d_letters and d_letters in clean_full_name and len(d_letters) >= 3:
                                    student_matched = True
                                elif first_name:
                                    if d_letters == first_name:
                                        student_matched = True
                                    elif len(d_letters) >= 3 and first_name.startswith(d_letters):
                                        student_matched = True
                                    elif len(first_name) >= 3 and first_name in d_letters:
                                        student_matched = True
                                    else:
                                        for part in valid_parts:
                                            if len(part) >= 3 and part in d_letters:
                                                student_matched = True
                                                break
                                                
                            if student_matched:
                                matched_in_this_file.add(record['raw'])
                                student_present_today = True
                                
                        if student_present_today:
                            master_df.at[index, 'Total Attendance'] += 1
                                
                    # Collect leftover unmatched names
                    for record in daily_records:
                        if record['raw'] not in matched_in_this_file:
                            all_unmatched_names.append(record['raw'])
                            
                else:
                    st.warning(f"File {file.name} mein 'Name' wala koi column nahi mila.")

            st.success("Attendance successfully calculate ho gayi hai! 🎉")
            
            # --- CALCULATING PRESENT & ABSENT ---
            total_students = len(master_df)
            present_today = (master_df['Total Attendance'] > 0).sum()
            absent_today = total_students - present_today
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric(label="🟢 Total Present", value=f"{present_today} / {total_students}")
            with col2:
                st.metric(label="🔴 Total Absent", value=f"{absent_today} / {total_students}")
            
            # --- Absent Students Dropdown ---
            if absent_today > 0:
                absent_df = master_df[master_df['Total Attendance'] == 0]
                with st.expander("🔴 Click here to view Absent Students List"):
                    for _, row in absent_df.iterrows():
                        st.write(f"❌ **{row.get('Student Name', 'Unknown')}** (ID: {row.get('pariticipant_id', 'N/A')})")
            
            # --- NAYA CODE: Unmatched Names Dropdown ---
            unique_unmatched = list(set(all_unmatched_names)) # Remove duplicates
            if unique_unmatched:
                with st.expander(f"⚠️ Unmatched Names (Daily file m hain, par Master m nahi): {len(unique_unmatched)}"):
                    st.write("Yeh naam Master sheet se match nahi hue (Guest, teacher, ya extra text ho sakte hain):")
                    for u_name in unique_unmatched:
                        st.write(f"❓ {u_name}")
            # ---------------------------------------------

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
