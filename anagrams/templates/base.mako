<html>
    <head>
        <script src="http://ajax.googleapis.com/ajax/libs/jquery/1.4.2/jquery.min.js"></script>
        <script src="http://ajax.googleapis.com/ajax/libs/jqueryui/1.8.2/jquery-ui.min.js"></script>
        <script src="/js/jquery.form.js"></script>
        <script type="text/javascript"> 
            document.domain = document.domain;
            // Load the hookbox.js from the current host but changing the port to 2974.
            server = location.protocol + '//' + location.hostname + ':8001';
            // Dynamically inserts the code to load the script into the page.
            document.write('<scr'+'ipt src="' + server + '/static/hookbox.js"></scr'+'ipt>');
%if c.user:
            password = "${c.user.password}"
%endif
        </script>
        <link rel="stylesheet" href="http://ajax.googleapis.com/ajax/libs/jqueryui/1.8.2/themes/ui-lightness/jquery-ui.css" type="text/css" />
    </head> 
    <body>
<%def name="title()">
    Anagrams
</%def>

${self.body()}

</body>
</html>
