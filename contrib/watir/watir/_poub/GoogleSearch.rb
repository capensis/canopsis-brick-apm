require 'rubygems'
require 'watir-webdriver'

Given /^that I have gone to the Google page$/ do
	@browser = Watir::Browser.new(:firefox)
	@browser.goto("https://www.google.com")
end

When /^I add (.*) to the search box$/ do |item|
	@browser.text_field(:name,"q").set( item)

end

And /^click the Search Button$/ do
	@browser.button(:name, "btnG").click
end

Then /^(.*) should be mentioned in the results$/ do |item|
	@browser.text.include? item 
end



