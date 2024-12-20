json {source => "message"}

mutate {
  add_field => {
      "[GuardRecord][sessionLocator][clientIp]" => "0.0.0.0"
      "[GuardRecord][accessor][clientHostName]" => "NA"
      "[GuardRecord][exception][sqlString]" => "NA"
      "[GuardRecord][exception][description]" => "NA"
      "[GuardRecord][dbName]" => "NA"
      "[GuardRecord][accessor][dbUser]" => "NA"
      "[GuardRecord][accessor][serverHostName]" => "mssql"
      "[GuardRecord][accessor][dataType]" => "TEXT"
      "[GuardRecord][accessor][osUser]" => ""
      "[GuardRecord][accessor][serverType]" => "MSSQL"
      "[GuardRecord][accessor][commProtocol]" => ""
      "[GuardRecord][accessor][dbProtocol]" => "MS SQL SERVER"
      "[GuardRecord][accessor][language]" => "MSSQL"
      "[GuardRecord][accessor][serverOs]" => ""
      "[GuardRecord][accessor][clientOs]" => ""
      "[GuardRecord][appUserName]" =>  ""
      "[GuardRecord][accessor][sourceProgram]" => "NA"
      "[GuardRecord][sessionLocator][clientPort]" => "-1"
      "[GuardRecord][sessionLocator][serverIp]" => "0.0.0.0"
      "[GuardRecord][sessionLocator][isIpv6]" => "false"
      "[GuardRecord][sessionLocator][serverPort]" => "%{server_port}"
      "[GuardRecord][accessor][dbProtocolVersion]" => ""
      "[GuardRecord][accessor][clientMac]" => ""
      "[GuardRecord][accessor][serverDescription]" => ""
      "[GuardRecord][accessor][serviceName]" => ""
      "[GuardRecord][time][minOffsetFromGMT]" => "0"
      "[GuardRecord][time][minDst]" => "0"
  }
}
if [succeeded] == "True" or [action_name] == "DATABASE AUTHENTICATION FAILED" {
  grok { match => { "event_time" => "%{YEAR:year}-%{MONTHNUM:month}-%{MONTHDAY:day}T%{TIME:time}" } }
  date {
      match => ["mssqlTimeStamp", "ISO8601"]
      target => "mssqlEventTime"
  }
   ruby { code => "event.set('[GuardRecord][time][timstamp]', event.get('mssqlEventTime').to_i * 1000)" }
  if [session_id]{
      mutate { add_field  => { "[GuardRecord][sessionId]" => "%{session_id}" }}
  }
  if [database_name]{
      mutate { replace  => { "[GuardRecord][dbName]" => "%{database_name}" }}
      mutate { replace  => { "[GuardRecord][accessor][serviceName]" => "%{database_name}" }}
  }
  if [server_principal_name]{
      mutate { replace => { "[GuardRecord][accessor][dbUser]" => "%{server_principal_name}" }}
  }
  if [server_instance_name]{
      mutate { replace => { "[GuardRecord][accessor][serverHostName]" => "%{server_instance_name}" }}
  }
  if [application_name]{
      mutate { replace => { "[GuardRecord][accessor][sourceProgram]" => "%{application_name}"} }
  }
  if [client_ip] != "local machine" or [client_ip] != "Unknown"{
      mutate { replace  => { "[GuardRecord][sessionLocator][clientIp]" => "%{client_ip}" }}
  }
  mutate {add_field => { "isSuccess" => "%{succeeded}" }}
  if [isSuccess] == "True" {
      ruby { code => 'event.set("[GuardRecord][data][construct]", nil)' }
      mutate { add_field => { "[GuardRecord][data][originalSqlCommand]" => "%{statement}" }}
        ruby { code => 'event.set("[GuardRecord][exception]", nil)' }
    }
    else {
        mutate { add_field => { "[GuardRecord][exception][exceptionTypeId]" => "LOGIN_FAILED" }}
        mutate { replace => { "[GuardRecord][exception][description]" => "%{statement}" }}
        ruby { code => 'event.set("[GuardRecord][data]", nil)' }
    }
} else if [succeeded] == "False" {
  xml {
      store_xml => "false"
      source => "event_data"
      remove_namespaces => "false"
      xpath => [
          "/event/action[@name='username']/value/text()", "db_user",
          "/event/action[@name='sql_text']/value/text()", "sql_string",
          "/event/action[@name='server_instance_name']/value/text()", "server_host_name",
          "/event/action[@name='session_id']/value/text()", "session_id",
          "/event/action[@name='database_name']/value/text()", "database_name",
          "/event/action[@name='client_hostname']/value/text()", "client_ip",
          "/event/data[@name='message']/value/text()", "error_description",
          "/event/data[@name='error_number']/value/text()", "error_number"
      ]
  }
 mutate {
     replace => [ "error_number", "%{error_number}"]
     convert => [ "error_number", "integer"]
  }
  if [error_number] >= 17000 and [error_number] < 19000 {
      drop { }
  }
  mutate {
      gsub => [
          "db_user", "<!\[CDATA\[", "",
          "db_user", "]]>", "",
          "sql_string", "<!\[CDATA\[", "",
          "sql_string", "]]>", "",
          "server_host_name", "<!\[CDATA\[", "",
          "server_host_name", "]]>", "",
          "database_name", "<!\[CDATA\[", "",
          "database_name", "]]>", "",
          "client_ip", "<!\[CDATA\[", "",
          "client_ip", "]]>", "",
          "error_description", "<!\[CDATA\[", "",
          "error_description", "]]>", ""
      ]
  }
  if [session_id]{
      mutate { add_field => { "[GuardRecord][sessionId]" => "%{session_id}" }}
  }
  if [database_name]{
      mutate { replace => { "[GuardRecord][dbName]" => "%{database_name}" }}
      mutate { replace  => { "[GuardRecord][accessor][serviceName]" => "%{database_name}" }}
  }
  if [db_user]{
      mutate { replace => {  "[GuardRecord][accessor][dbUser]" => "%{db_user}" }}
  }
  if [server_host_name]{
      mutate { replace => {  "[GuardRecord][accessor][serverHostName]" => "%{server_host_name}" }}
  }
  if [sql_string]{
      mutate { replace => {"[GuardRecord][exception][sqlString]" => "%{sql_string}" }}
  }
  if [error_description]{
      mutate { replace => { "[GuardRecord][exception][description]" => "%{error_description}" }}
  }
  mutate {
      add_field => {"[GuardRecord][exception][exceptionTypeId]" => "SQL_ERROR" }
      replace => [ "client_ip", "%{client_ip}"]
  }
  if [client_ip] =~ /(?<![0-9])(?:(?:[0-1]?[0-9]{1,2}|2[0-4][0-9]|25[0-5])[.](?:[0-1]?[0-9]{1,2}|2[0-4][0-9]|25[0-5])[.](?:[0-1]?[0-9]{1,2}|2[0-4][0-9]|25[0-5])[.](?:[0-1]?[0-9]{1,2}|2[0-4][0-9]|25[0-5]))(?![0-9])/ {
      mutate { replace => { "[GuardRecord][sessionLocator][clientIp]" => "%{client_ip}" }}
  } else if [client_ip] =~ /\b(?:[0-9A-Za-z][0-9A-Za-z-]{0,62})(?:\.(?:[0-9A-Za-z][0-9A-Za-z-]{0,62}))*(\.?|\b)/ {
      mutate { replace => { "[GuardRecord][accessor][clientHostName]" => "%{client_ip}" }}
  }
  ruby { code => "event.set('[GuardRecord][time][timstamp]', event.get('timestamp_utc').to_i * 1000)" }
  ruby { code => 'event.set("[GuardRecord][data]", nil)' }
} else {
    mutate {
        add_field => { "[GuardRecord][debug_succeeded]" => "%{succeeded}"}
    }
}
ruby { code => 'event.set("[GuardRecord][sessionLocator][clientIpv6]", nil)' }
ruby { code => 'event.set("[GuardRecord][sessionLocator][serverIpv6]", nil)' }
mutate {
  convert => {"[GuardRecord][sessionLocator][clientPort]" => "integer"}
  convert => {"[GuardRecord][sessionLocator][serverPort]" => "integer"}
  convert => {"[GuardRecord][sessionLocator][isIpv6]" => "boolean"}
  convert => {"[GuardRecord][time][minOffsetFromGMT]" => "integer"}
  convert => {"[GuardRecord][time][minDst]" => "integer"}
}
prune {
  whitelist_names => [ "GuardRecord" ]
}
mutate {
  convert => { "[GuardRecord]" => "string" }
}
json_encode {
  source => "[GuardRecord]"
}