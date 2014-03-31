require 'rubygems'
require 'watir-webdriver'
require 'watir-webdriver/wait'
require 'headless'
World(RSpec::Matchers)

@headless = true

if ENV['HEADLESS'] and ENV['HEADLESS'] == false
	@headless = false
end

if @headless
	require 'headless'
	headless = Headless.new
	headless.start
	@browser = Watir::Browser.new(:firefox)
	at_exit do
		headless.destroy
	end
end
