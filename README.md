# Odoo_Thesis_Design_Database_Manager
A database manager that updates the status of the studies of thesis/design groups as well as informs studies with similar parameters

# launch.json default::(auto upgrade database manager)
{
    // Use IntelliSense to learn about possible attributes.
    // Hover to view descriptions of existing attributes.
    // For more information, visit: https://go.microsoft.com/fwlink/?linkid=830387
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: Odoo17",
            "type": "python",
            "request": "launch",
            "stopOnEntry": false,
            "pythonPath": "C:\\Program Files\\Odoo 17.0.20240628\\python\\python.exe", // path of python in your local machine where odoo has installed
            "console": "integratedTerminal",
            "program": "${workspaceRoot}\\odoo-bin",
            "args": [
                "--config=${workspaceRoot}\\odoo.conf",
                "-d", "odoo17_training",
                "-u", "thesis_design_database_manager"
            ],
            "cwd": "${workspaceRoot}",
            "env": {},
            "envFile": "${workspaceRoot}/.env",
            "debugOptions": [
                "RedirectOutput"
            ]
        }
    ]
}

# For installation of panadas
## launch.json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: Odoo17",
            "type": "python",
            "request": "launch",
            "stopOnEntry": false,
            "pythonPath": "C:\\Program Files\\Odoo 17.0.20240628\\python\\python.exe", // path of python in your local machine where odoo has installed
            "console": "integratedTerminal",
            "program": "${workspaceRoot}\\odoo-bin",
            "args": [
                "--config=${workspaceRoot}\\odoo.conf",
                "-d", "odoo17_training",
                "-u", "thesis_design_database_manager" //comment out if necessary
            ],
            "cwd": "${workspaceRoot}",
            "env": {},
            "envFile": "${workspaceRoot}/.env",
            "preLaunchTask": "install pandas and openpyxl",
            "debugOptions": [
                "RedirectOutput"
            ]
        }
    ]
}
## task.json
//task.json (add as new file)
{
    "version": "2.0.0",
    "tasks": [
        {
            "label": "install pandas and openpyxl",
            "type": "shell",
            "command": "C:\\Program Files\\Odoo 17.0.20240628\\python\\python.exe", // specify the full path to your Python interpreter
            "args": [
                "-m",
                "pip",
                "install",
                "pandas",
                "openpyxl"
            ],
            "group": {
                "kind": "build",
                "isDefault": true
            },
            "problemMatcher": []
        }
    ]
}
