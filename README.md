# Coursera Parser 

## Description 

This program allows you to download courses from Coursera. 

## How to use

There are three commands: `login`, `get-course-data`, and `download-course`. If you want to download a course, you must follow these instructions:

1. Sign in to your account using the `login` command.
2. Download information about the course using the `get-course-data` command into a JSON file.
3. Finally, apply the `download-course` command to your JSON file.




## Examples
1. `pip install -r requirements.txt` <br>
  This command will install the required libraries.


2. `python main.py login --email <EMAIL> --password <PASSWORD>` <br>
  This command saves your cookies into _./cookies/last-saved.pkl_. Additionally, you can use the parameter `--file-name <FILENAME>.pkl` to save your cookies to _./cookies/\<FILENAME\>.pkl_.

3. `python main.py get-course-data -u <url>` <br>
  As a result of this command, all data about the course will be downloaded to _./download/<COURSE_NAME>.json_. <br>
  Usually, `<url>` looks like `https://www.coursera.org/learn/<COURSE_NAME>/home/week/1`. **You don't need to apply this command for all weeks.** The algorithm looks at the first page, calculates the number of weeks, and parses all courses. <br>
  If you use `--file-name` in the `login` command, then you can add `--cookies <FILENAME>.pkl` to select a different session.

4. `python main.py download-course -p <path_to_data>.json`
After applying this command, all course data will be downloaded to _./downloads/<COURSE_NAME>/_. <br>
Like previous section, there you also can use `--cookies` to select appropriate session.



## Issues:
1. Sometimes Coursera changes its website code, so the parser may break until I update the web element paths.
 

2. If you see an exception like this _"AssertionError: Unrecognized lesson type Peer-graded Assignment"_ (where _Peer-graded Assignment_ may be replaced by another lesson type), simply set `DEBUG = False` in defines.py.

3. You can only use the English version of the website. To change the website language, go to Settings.