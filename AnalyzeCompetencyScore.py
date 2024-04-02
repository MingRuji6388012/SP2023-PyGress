import subprocess
import os
import shutil
import csv
import time
import glob

def clone_repository():
    print("Step 1: Clone PyCEFR repo")
    if not os.path.exists('pycefr'):  # Check if directory exists
        subprocess.run(['git', 'clone', 'https://github.com/anapgh/pycefr.git'])
        print("Successfully cloned pycefr\n")
    else:
        print("Directory 'pycefr' already exists. Skipping cloning.\n")

def create_directory(directory_name):
    print(f"Step 2: Create directory: {directory_name}")
    if not os.path.exists(directory_name):  # Check if directory exists
        os.makedirs(directory_name, exist_ok=True)
        print(f"Successfully created {directory_name}\n")
    else:
        print(f"Directory '{directory_name}' already exists. Skipping creation.\n")

def create_csv_files():
    print(f"Step 3: Create csv files (filtered_all_projects.csv)")
    if not os.path.exists('filtered_all_projects.csv'):  # Check if file exists
        with open('DataPyPI.csv', 'r', encoding='utf-8') as input_file, \
             open('filtered_all_projects.csv', 'w', newline='', encoding='utf-8') as output_file:
            reader = csv.reader(input_file)
            writer = csv.writer(output_file)
            writer.writerow(['URL', 'ProjectName', 'Path', 'Status', 'DeadAliveStatus'])  # Include 'DeadAliveStatus' field in the header
            next(reader)  # Skip the header row in DataPyPI.csv
            for row in reader:
                url, project_name = row[0], row[1]
                path = f'../PythonFiles/{project_name}'
                writer.writerow([url, project_name, path, '', ''])  # Include empty strings for 'Status' and 'DeadAliveStatus'
        print(f"Successfully created csv files filtered_all_projects.csv\n")
    else:
        print("File 'filtered_all_projects.csv' already exists. Skipping creation.\n")

def change_directory(directory_name):
    time.sleep(0.5)
    print(f"Step 4: Change Directory to PyCEFR\n")
    os.chdir(directory_name)

def run_dict_py():
    print(f"Step 5: Run dict.py\n")
    subprocess.run(['python3', 'dict.py'])

def append_to_csv(source_file, target_file, header=None):
    """Append contents of source_file to target_file."""
    with open(source_file, 'r', encoding='utf-8') as source:
        with open(target_file, 'a', newline='', encoding='utf-8') as target:
            reader = csv.reader(source)
            writer = csv.writer(target)

            if os.path.getsize(target_file) == 0 and header is not None:
                # Write header only if the target file is empty and header is provided
                writer.writerow(header)

            next(reader)  # Skip header in source file
            for row in reader:
                if any(field.strip() for field in row):  # Check if any field is non-blank
                    writer.writerow(row)

def analyze_projects():
    print(f"Step 6: Analyze the projects\n")
    
    # Read the existing counts from the previous run
    done_count = 0
    done_count_dup = 0
    undone_count = 0
    undone_count_dup = 0

    # Truncate all_projects_done.csv and all_projects_undone.csv to remove all records except header
    with open('../all_projects_done.csv', 'w', newline='', encoding='utf-8') as done_file:
        writer = csv.DictWriter(done_file, fieldnames=['URL', 'ProjectName', 'Path', 'Status', 'DeadAliveStatus'])
        writer.writeheader()  # Write header

    with open('../all_projects_undone.csv', 'w', newline='', encoding='utf-8') as undone_file:
        writer = csv.DictWriter(undone_file, fieldnames=['URL', 'ProjectName', 'Path', 'Status', 'DeadAliveStatus'])
        writer.writeheader()  # Write header

    # Append new records to all_projects_done.csv and all_projects_undone.csv
    done_projects = []
    undone_projects = []

    with open('../filtered_all_projects.csv', 'r', encoding='utf-8') as all_projects_file:
        reader = csv.DictReader(all_projects_file)
        for row in reader:
            if row['Status'] == 'Succeeded':
                done_projects.append(row)
            elif row['Status'] == 'NotSucceeded':
                undone_projects.append(row)

    # Append new records to all_projects_done.csv
    with open('../all_projects_done.csv', 'a', newline='', encoding='utf-8') as done_file:
        writer = csv.DictWriter(done_file, fieldnames=['URL', 'ProjectName', 'Path', 'Status', 'DeadAliveStatus'])
        if done_projects:
            writer.writerows(done_projects)

    # Append new records to all_projects_undone.csv
    with open('../all_projects_undone.csv', 'a', newline='', encoding='utf-8') as undone_file:
        writer = csv.DictWriter(undone_file, fieldnames=['URL', 'ProjectName', 'Path', 'Status', 'DeadAliveStatus'])
        if undone_projects:
            writer.writerows(undone_projects)

    # Delete existing CompetencyScore files for projects with status not 'Succeeded'
    with open('../filtered_all_projects.csv', 'r', encoding='utf-8') as all_projects_file:
        reader = csv.DictReader(all_projects_file)
        for row in reader:
            if row['Status'] != 'Succeeded':
                project_name = row['ProjectName']
                file_path = f'../CompetencyScore/{project_name}_CompetencyScore.csv'
                if os.path.exists(file_path):
                    os.remove(file_path)
    
    # Continue with the analysis
    all_projects = []  # Define an empty list to store project data

    if os.path.exists('../all_projects_done.csv'):
        with open('../all_projects_done.csv', 'r', encoding='utf-8') as done_file:
            done_count = sum(1 for line in done_file) - 1  # Subtracting 1 to exclude the header
            done_count_dup = done_count
    if os.path.exists('../all_projects_undone.csv'):
        with open('../all_projects_undone.csv', 'r', encoding='utf-8') as undone_file:
            undone_count = sum(1 for line in undone_file) - 1  # Subtracting 1 to exclude the header
            undone_count_dup = undone_count

    print("\n==============================================================")
    print("==============================================================\n")
    print(f"Number of successfully recorded projects: {done_count}")
    print(f"Number of unsuccessfully recorded projects: {undone_count}")
    print("\n==============================================================")
    print("==============================================================\n")

    with open('../filtered_all_projects.csv', 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            all_projects.append(row)  # Add each project row to the list

    for row in all_projects:
        done_project_flag = 0
        if row['Status'] != 'Succeeded':  # Check if the status is not already "Succeeded"
            print(f"\nGoing to project: {row['ProjectName']}")
            project_name = row['ProjectName']
            path = row['Path']
            
            # Skip if Path is empty
            if not path:
                print(f"Skipping project: {project_name} as its path is empty")
                done_project_flag = 1
                continue
            
            project_path = os.path.join('../PythonFiles', project_name).replace("\\", "/")
            
            # Check if the project path exists
            if not os.path.exists(project_path):
                print(f"Project path '{project_path}' does not exist for project: {project_name}")
                done_project_flag = 1
                continue
            
            # Traverse through the project directory
            for author_id in os.listdir(project_path):
                time.sleep(0.5)
                author_path = os.path.join(project_path, author_id).replace("\\", "/")
                
                # Check if the author directory exists
                if not os.path.isdir(author_path):
                    done_project_flag = 1
                    continue
                
                for commit_dir in os.listdir(author_path):
                    commit_path = os.path.join(author_path, commit_dir).replace("\\", "/")
                    
                    # Check if the commit directory exists
                    if not os.path.isdir(commit_path):
                        done_project_flag = 1
                        continue

                    print(f"\nAnalyzing commit directory: {commit_path}\n")
                    
                    try:
                        # Run analysis on the commit directory using subprocess
                        result = subprocess.run(['python3', 'pycerfl.py', 'directory', commit_path], capture_output=True)
                        print(f"result: {result}\n")
                        
                        print(f"Successfully analyzed commit directory: {commit_path}\n")
                        print(f"==============================================================================================")
                        
                        # Copy the result to the CompetencyScore directory
                        target_file = f'../CompetencyScore/{project_name}_CompetencyScore.csv'
                        append_to_csv('data.csv', target_file, header=['Repository', 'File Name', 'Class', 'Start Line', 'End Line', 'Displacement', 'Level'])
                        
                    except UnicodeDecodeError as e:
                        print(f"UnicodeDecodeError occurred: {e}. Skipping this directory.")
                        done_project_flag = 1
                        continue

            if done_project_flag == 0:
                row['Status'] = 'Succeeded'
                done_count += 1

            else:
                row['Status'] = 'NotSucceeded'
                undone_count += 1


            # Update the status for the current project
            with open('../filtered_all_projects.csv', 'w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=['URL', 'ProjectName', 'Path', 'Status', 'DeadAliveStatus'])
                writer.writeheader()
                writer.writerows(all_projects)

            print("\n\n\n\tProjects analysis complete.\n\n\n")
            # Update the status to 'Succeeded' in all_projects.csv


            # Print and record the count of done and undone projects
            print("\n==============================================================")
            print("==============================================================\n")
            print(f"Number of successfully recorded projects: {done_count}")
            print(f"Number of unsuccessfully recorded projects: {undone_count}")
            print("\n==============================================================")
            print("==============================================================\n")

            with open('../projects_counts.txt', 'w') as txt_file:
                txt_file.write(f"Number of successfully recorded projects: {done_count}\n")
                txt_file.write(f"Number of unsuccessfully recorded projects: {undone_count}\n")

    # Step 7: calculate_competencyScore
def calculate_competencyScore():
    print("Step 7: Calculate CompetencyScore")
    # Call the main function from the competencyScore script
    subprocess.run(['python3', 'CalculateCompetencyScore.py'])


if __name__ == "__main__":
    clone_repository()
    create_directory("CompetencyScore")
    create_csv_files()
    change_directory("pycefr")
    run_dict_py()
    analyze_projects()
    calculate_competencyScore()  # Step 7: 
