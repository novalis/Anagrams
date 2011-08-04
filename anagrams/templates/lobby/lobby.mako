<%inherit file="../base.mako" />

      <style>
        .disabled {
        color: #ccc;
        }
      </style>

      <script type="text/javascript">
        if (typeof console == "undefined" || typeof console.log == "undefined") var console = { log: function() {} };  
        $(document).ready(
        function() {
        
        /* set up the form */
        $("#form").ajaxForm();
        $("#accept_form").ajaxForm({'beforeSubmit' : function() {
          $("#accept").hide();
        }});
        $(".hidden").hide();

        /* set up the hookbox hooks */
	var my_display_name = '${c.user.display_name}';
	var my_id = ${c.user.id};
        var conn = hookbox.connect('${c.hookbox_server}');
        conn.onOpen = function() { 
          conn.subscribe("/lobby");
          conn.subscribe(password); //user's personal queue
          conn.subscribe("/heartbeat");
        };

        conn.onError = function(err) {

           //TODO:reconnect
           alert("connection failed: " + err.msg); 
        };

        var subscription = null;

        conn.onSubscribed = function(channelName, _subscription) {

            subscription = _subscription;                

            subscription.onPublish = function(frame) {
        
                console.log("got ", frame.payload);
                var message = frame.payload;
                var type = message.type;
                var user = message.user;

                if (type == 'enter') {
                  var display_name = user.display_name;
		  console.log("here");
		  console.log(user);
		  console.log(display_name);

	          var id = 'user_' + user.id;
	          if (!($('#' + id).length)) {
                    var new_user = '<li id="' + id + '">';
                    new_user += '<input type="checkbox" value="' + user.id + '" id="check_' + user.id + '" name="invite" class="invitee"> ';
                    new_user += '<label for="check_' + user.id + '">' + display_name + '</label></li>';
                    $('#users').append(new_user);
                  }

                } else if (type == 'leave') {
                  $("#user_" + user.id).remove()

                } else if (type == 'disable') {
                  $("#user_" + user.id).addClass("disabled")

                } else if (type == 'enabled') {
                  $("#user_" + user.id).removeClass("disabled")

                } else if (type == 'message') {
                  $('#ticker').append(message.message);

                } else if (type == 'invite') {
                  var others = "";
                  if (message.other_players.length != 0) {
                     others = "with " + message.other_players.join(", ");
                  }
                  var text;
                  if (message.inviter.id == my_id)  {
		      if (!others) {
		          others = "yourself";
		      }
                      text = "<div>You invited " + others + " to a game (min word length " + message.min_word_len + ")</div>"; 
                  } else {
                      text = "<div>You have been invited by " + message.inviter + " to a game " + others + " (min word length " + message.min_word_len + ")</div>";
                  }
                  $('#ticker').append(text);
                  $('#ticker').append($('#accept'));
                  $('#accept').show();
                } else if (type == 'begin') {
                  window.location.href = "${h.url(action='game', controller='game')}";
                }
              };
              if (channelName == "/lobby") {
                var message = {'payload' : ${c.initial_data | n} };
		if (message.payload) {
		    subscription.onPublish(message);
                }
              }
           }
        
        });
        </script>


<div id="ticker"></div>
<div id="accept" class="hidden">
${h.secure_form(url(action="accept", controller="lobby"), id="accept_form")}
<input type="submit" name="accept" value="accept" />
<input type="submit" name="accept" value="decline" />
</form>
</div>

${h.secure_form(url(action="invite", controller="lobby"), id="form")}

Minimum word length: <input type="text" value="5" name="min_word_len" />
<input type="submit" value="invite" name="" />

<ul id="users">
% for user in c.free_users:
% if user != c.user:
    <li id="user_${user.id}">
      <input type="checkbox" name="invite" value="${user.id}" class="invitee" id="check_${user.id}">
      <label for="check_${user.id}">${user.display_name}</label>
    </li>
% endif
% endfor
</ul>

</form>
