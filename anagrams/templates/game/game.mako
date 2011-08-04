<%inherit file="../base.mako" />

<style>
.disabled {
color: #ccc;
}
.wordbox {
border: 1px solid black;
float: left;

margin:10px;
padding:5px;
-webkit-column-count: 2;
-webkit-column-width: 160px;
-moz-column-count: 2;
-moz-column-width: 160px;
column-count: 2;
column-width: 160px;
width:340px;

}
</style>

<script type="text/javascript">
        if (typeof console == "undefined" || typeof console.log == "undefined") console = { log: function() {} };
  game_channel = "${c.game.channel}";

  function handleGameStatus(data) {
    console.log("handle data", data)
    for (item in data) {
        item = data[item];
        if (!item) continue;
	var username = "";
	var user_id = "";
	if ( item.user) {
	    username = item.user.display_name;
	    user_id = item.user.id;
	}
        var words_el = $("#words_" + user_id);
        var word = item.word;
        var id = user_id + "_" + word;

        if (item.type == "add") {
          word_el = '<div class="word" id = "' + id + '">';
          word_el += '<input type="checkbox" name="word" id="cb_' + id + '" value="' + id + '">';
          word_el += '<label for="cb_' + id + '">' + word + "</label>"
          word_el += "</div>"
          words_el.append(word_el);
        } else if (item.type == "remove") {
          $('#' + id).remove();
        } else if (item.type == "center") {
          $("#center").html(item.letters);
	  $("#center").stop()
	  $("#center").css('backgroundColor', '#f00');
	  $("#center").animate({ backgroundColor: '#fff' }, 2000);

          $("#bag").html(item.bag);
          if (item.bag == 0) {
            $('#turnup_button').attr('disabled', 'disabled');
            $('#done_button').val("return to lobby");
          }
        } else {
          console.log("unknown item type", item);
        }
    }
  }

  function updateTicker(message) {
      var ticker = $('#ticker');
      ticker.append("<div>" + message + "</div>");
      ticker.animate({ scrollTop: ticker.attr("scrollHeight") - ticker.height() + 30 }, 30);
  }

  $(document).ready(
  function() {
  
  /* set up the form */
  $("#form").ajaxForm({ 
    'dataType' : 'json',
    'success' : function(data) {
      if (data.type == "failure") {
        updateTicker(data.message);
      } else {
              $('#form')[0].reset();
      }
    }});


  $("#chat").ajaxForm({
    'success' : function(data) {
      $("#chat")[0].reset();
    }
  });
  $("#turnup").ajaxForm();
  $(".hidden").hide();
  
  /* set up the hookbox hooks */
  
  var conn = hookbox.connect('${c.hookbox_server}');
  conn.onOpen = function() { 
    conn.subscribe(password); //user's personal queue
    conn.subscribe(game_channel); //game queue
    conn.subscribe("/heartbeat");
    $.ajax({
      'url' : "/game/status",
      'dataType' : 'json',
      'success' : function(data) {
        handleGameStatus(data);
      }
    });
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
          if (!message.type) {
              message = jQuery.parseJSON(message);
          }
          var type = message.type;
          var user = message.user;
          if (type == 'status') {
            handleGameStatus(message.status);
          } else if (type == 'center') {
            handleGameStatus([message]);
          } else if (type == 'message') {
            updateTicker(message.message);
          } else if (type == 'bag_empty') {
            updateTicker("The bag is empty");
            $('#turnup_button').attr('disabled', 'disabled');
            $('#done_button').val("return to lobby");
          } else if (type == 'game_over') {
            updateTicker("The game is over");
          }
        };
    }
  });
</script>

${h.secure_form(url(action="play", controller="game"), id="form")}
% for user in c.game.users:
<div class="wordbox">
Words for ${user.display_name}:
<div id="words_${user.id}">


</div>
</div>
% endfor
<br clear="all" />

<div id="center_wrapper">
  Letters in center:
  <span id="center">${c.game.center}</span>
  Letters in bag:
  <span id="bag">${len(c.game.bag)}</span>
</div>

<input type="text" name="play" /> 
<input type="submit" value="play" id="playinput" name="submit" />

</form>

${h.secure_form(url(action="turnup", controller="game"), id="turnup")}
<input type="submit" value="Turn up a new letter" name=""  id="turnup_button" />
</form>


<div id="ticker" style="overflow:scroll; height: 15ex;max-height:15ex;"></div>

${h.secure_form(url(action="chat", controller="game"), id="chat")}
<input type="text" name="chat" size="60" /> 
<input type="submit" value="chat" name="" />

</form>


${h.secure_form(url(action="done", controller="game"), id="chat")}
<input type="submit" value="resign" name="" id="done_button" />
</form>
