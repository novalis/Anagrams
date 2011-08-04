${h.secure_form(url(action='setup', controller='user'))}
  Logged in with email address: ${c.user.email}<br/>
  Display name: <input name="display_name" type="text" value="${c.display_name}"><br/>

  <input name="submit" type="submit" value="Log in"><br/>
</form>
