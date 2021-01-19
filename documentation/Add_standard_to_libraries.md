IriusRisk Toolkit UI : Add standard to libraries
=======================================================================    
 
Launch IriusRiskToolkitUI by executing the following command:  
  
``` 
python IriusRiskToolKitUI.py
```

This will open a GUI. Among them is the option "Add Standard to library or libraries":

![](attachments/1053098013/1053130788.png)

This option has three possible choices:

* Export standards to CSV: A CSV file composed by six columns (Library, Component, Control, Supported Standard Name, Supported Standard Ref, Standard Ref) will be created in inputFiles/standardsFiles/standardEditor.csv, except if you indicate a different file with the “Select CSV” browse option.
* Add standards to library using CSV: Once the exported CSV has been modified leaving only those controls that need a standard this file will be used to modify the selected library.
* Delete standards to library using CSV: Same as before, but removing the standards from the controls listed in the CSV file.

The library to work with can be selected using the browse button:

![](attachments/1053098013/2d1bc4dd-600c-4ab0-b420-89549737d00b.png)

**Note**: If no library is selected the process will go through every library in /libraries folder inside the toolkit.

Depending of the selected choice the result will be a message indicating where are the files saved:

![](attachments/1053098013/9daaaa95-b024-4468-afcd-69516405597c.png)

The workflow to use this process should be the following:
* First step is to export all standards from the desired library or from all libraries
* After that you need to edit the standardEditor.csv file to add or remove rows as you wish
* Once you finish editing the CSV you will have to use the options "Add" or "Delete" on the menu above
  * This options will go through every row on the modified CSV and add or delete the standard on the corresponding countermeasures.

**Important**: "Add standards..." option is an additive process, meaning that the process to add new rows will work whether the CSV contains all the previously exported rows plus the new ones or only the new ones. This is not a big deal when adding but it won't work the same when deleting. You must ensure that if you want to remove standards you must only have the rows to be deleted in the CSV. 


[Back to index](Readme.md)