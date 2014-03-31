# -*- encoding: utf-8 -*-

Gem::Specification.new do |s|
  s.name = "amq-protocol"
  s.version = "1.9.2"

  s.required_rubygems_version = Gem::Requirement.new(">= 0") if s.respond_to? :required_rubygems_version=
  s.authors = ["Jakub Stastny", "Michael S. Klishin", "Theo Hultberg", "Mark Abramov"]
  s.date = "2013-12-20"
  s.description = "  amq-protocol is an AMQP 0.9.1 serialization library for Ruby. It is not an\n  AMQP client: amq-protocol only handles serialization and deserialization.\n  If you want to write your own AMQP client, this gem can help you with that.\n"
  s.email = ["michael@novemberain.com", "stastny@101ideas.cz"]
  s.extra_rdoc_files = ["README.md"]
  s.files = ["README.md"]
  s.homepage = "http://github.com/ruby-amqp/amq-protocol"
  s.licenses = ["MIT"]
  s.require_paths = ["lib"]
  s.rubyforge_project = "amq-protocol"
  s.rubygems_version = "2.0.0"
  s.summary = "AMQP 0.9.1 encoder & decoder."
end
