The script takes in 5 parameters:
'-o': 'Path to the origin html document that contains the original element'
'-m': 'Path to diff-case HTML file to search a similar element'
'-t': 'Type of target element in the original page. E.g. "a", "div", etc.' ***OPTIONAL
'-n', 'Name of an attribute of the target element. E.g. "class", "title", etc.'
'-v', 'Value of the attribute of the target element. E.g. "btn btn-success"'

the output goes to stdout

Use example:
python3 main.py -o path\to\sample-0-origin.html -m path\to\sample-1-evil-gemini.html -n id -v make-everything-ok-button

Similarity weights
    id = 100%
    if elements have identical parents - the weight of this attribute is doubled
    all other weights are standard, because the algorithm works OK even without that
