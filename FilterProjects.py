import csv

def read_csv(file_path):
    data = []
    with open(file_path, 'r', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            data.append(dict(row))
    return data

def add_dead_alive_status(all_projects_file, death_and_alive_file):
    # Read data from CSV files
    all_projects_data = read_csv(all_projects_file)
    death_and_alive_data = read_csv(death_and_alive_file)

    # Create a dictionary to store the DeadAliveStatus for each project
    dead_alive_status_dict = {row['ProjectName']: row['DeadAliveStatus'] for row in death_and_alive_data}

    # Filter out projects with DeadAliveStatus 'unknown'
    filtered_projects_data = [project for project in all_projects_data if project['ProjectName'] in dead_alive_status_dict]

    # Add DeadAliveStatus column to filtered projects
    for project in filtered_projects_data:
        project['DeadAliveStatus'] = dead_alive_status_dict.get(project['ProjectName'], '')

    return filtered_projects_data

def write_csv(data, output_file):
    fieldnames = data[0].keys()
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in data:
            writer.writerow(row)

def find_unmatched_projects(all_projects_file, death_and_alive_file):
    # Read data from CSV files
    all_projects_data = read_csv(all_projects_file)
    death_and_alive_data = read_csv(death_and_alive_file)

    # Create a set of project names from all_projects.csv
    all_project_names = {row['ProjectName'] for row in all_projects_data}

    # Find project names from Dead_Alive_Projects_Final.csv that do not have a matching entry in all_projects_data
    unmatched_project_names = [row['ProjectName'] for row in death_and_alive_data if row['ProjectName'] not in all_project_names]

    return unmatched_project_names

def main():
    all_projects_file = 'all_projects.csv'
    death_and_alive_file = 'Dead_Alive_Projects_Final.csv'
    filtered_all_projects_file = 'filtered_all_projects.csv'
    unmatched_project_names_file = 'unmatched_project_names.csv'

    # Add DeadAliveStatus to filtered projects
    projects_with_status_data = add_dead_alive_status(all_projects_file, death_and_alive_file)

    # Write the filtered records to a new CSV file
    write_csv(projects_with_status_data, filtered_all_projects_file)
    print(f"Filtered projects written to {filtered_all_projects_file}")

    # Find project names from all_projects.csv that do not have a matching entry in Dead_Alive_Projects_Final.csv
    unmatched_projects = find_unmatched_projects(all_projects_file, death_and_alive_file)

    # Write unmatched project names to a new CSV file
    write_csv([{'ProjectName': name} for name in unmatched_projects], unmatched_project_names_file)
    print(f"Unmatched project names written to {unmatched_project_names_file}")

if __name__ == "__main__":
    main()
