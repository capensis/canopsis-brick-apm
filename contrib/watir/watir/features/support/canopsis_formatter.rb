require "rubygems"
require "json"
#require "amqp"
#require "mq"
require "bunny"

module EUE
	class Canopsis

		@document = nil
		@feature_name = nil
		@scenario_name = nil
		@erreur = true
		
		@option_robot = "ROBOT_NC"
		@option_env = ""
		@option_os = "OS_NC"
		@option_browser = "BROWSER_NC"
		@option_localization = "LOCALIZATION_NC"
		
		@document_scenario = nil
		@scenario_step = 0


		def canopsis_escape_string( item )
			return item.gsub(/(\.|-|\"|\'|http:\/\/)/, "").gsub(/\s+/, "-").gsub(/%/, ".")
		end

		def cucumber2amqp( document )
			@rk = document['connector'] + '.' + document['connector_name'] + '.' + document['event_type'] + '.' + document['source_type'] + '.' + document['component'] + '.' + document['resource']
			
			print @rk
			print "\n"

			documentString = JSON.dump document

			conn = Bunny.new( :host => "192.168.250.250", :vhost => "canopsis" )
			conn.start
			chan = conn.create_channel
			exch = chan.topic("canopsis.events", :auto_delete => false, :durable => true)
			exch.publish( documentString, :routing_key => @rk )
			conn.close
		end

		def initialize(istep_mother, io, options={})

			if ENV['OPTION']
				@file = File.expand_path(File.dirname(__FILE__)+"/../../conf/"+ENV['OPTION']+".json")
				if  File.exists?( @file )
					options = JSON.parse( File.read( @file ) )
					@option_env = options['cntxt_env'] if options.key?('cntxt_env')
					@option_os = options['cntxt_os'] if options.key?('cntxt_os')
					@option_browser = options['cntxt_browser'] if options.key?('cntxt_browser')
					@option_localization = options['cntxt_localization'] if options.has_key?('cntxt_localization')
					@option_robot = options['robot'] if options.key?('robot')
				else
					print "FILE NOT FOUND"
					@erreur = true
				end
			end
			if ENV['APP']
				@app = ENV['APP']
			else
				print "No APP Name specified"
				@erreur = true
			end
		end

		def before_feature(feature)
			if not @erreur
				@feature_name = feature.title

				document =  {
					'connector'			=> 'cucumber',
					'connector_name'	=> @option_robot,
					'event_type'		=> 'eue',
					'source_type'		=> 'resource',
					'component'			=> @app,
					'resource'			=> canopsis_escape_string( @feature_name ),
					'type_message'		=> 'feature',

					'description'		=> feature.description,

					'state'				=> 0,
					'uniqId'			=> 'bonjour' 
				}
				
				cucumber2amqp( document )
			end
		end

		def scenario_name(keyword, name, file_colon_line, source_indent)
			if not @erreur
				@scenario_name = name

				@document_scenario =  {
					'connector'			=> 'cucumber',
					'connector_name'	=> @option_robot,
					'event_type'		=> 'eue',
					'source_type'		=> 'resource',
					'component'			=> @app,
					'resource'			=> canopsis_escape_string( @feature_name + "%" + @scenario_name + "%" + @option_localization + "%" + @option_os + "%" + @option_browser ),
					'type_message'		=> 'scenario',

					'cntxt_env'			=> @option_env,
					'cntxt_os'			=> @option_os,
					'cntxt_browser'		=> @option_browser,
					'cntxt_localization'=> @option_localization,

					'state'				=> 0,
					'uniqId'			=> 'bonjour',


				}
				@document_scenario['child'] = @document_scenario['connector'] + '.' + @document_scenario['connector_name'] + '.' + @document_scenario['event_type'] + '.' + @document_scenario['source_type'] + '.' + @document_scenario['component'] + '.' + canopsis_escape_string( @feature_name )
			end
		end

		def after_step(step)
			if not @erreur 
				@scenario_step = @scenario_step.to_i() + 1
				
				document =  {
					'connector'			=> 'cucumber',
					'connector_name'	=> @option_robot,
					'event_type'		=> 'eue',
					'source_type'		=> 'resource',
					'component'			=> @app,
					'resource'			=> canopsis_escape_string( @feature_name + "%" + @scenario_name + "%" + @scenario_step.to_s() + ' ' + step.name + "%" + @option_localization + "%" + @option_os + "%" + @option_browser ),
					'type_message'		=> 'step',

					'state'				=> 0,
					'uniqId'			=> 'bonjour',
				}
				document['child'] = document['connector'] + '.' + document['connector_name'] + '.' + document['event_type'] + '.' + document['source_type'] + '.' + document['component'] + '.' + canopsis_escape_string( @feature_name + "%" +     @scenario_name + "%" + @option_localization + "%" + @option_os + "%" + @option_browser )
		
				if step.status.to_s() == "failed"
					document['state'] = 2
				elsif step.status.to_s() == "passed"
					document['state'] = 0
				elsif step.status.to_s() == "skipped"
					document['state'] = 1
				elsif step.status.to_s() == "undefined"
					document['state'] = 3
				end
				if @document_scenario['state'] == 0 and document['state'] > 0
					@document_scenario['state'] = 2
				end
				print 'toto'
				cucumber2amqp( document )
			end
		end
		def after_steps(step)
			if not @erreur 
				print 'tata'
				cucumber2amqp( @document_scenario )
				@scenario_step = 0
			end
		end

	end
end
