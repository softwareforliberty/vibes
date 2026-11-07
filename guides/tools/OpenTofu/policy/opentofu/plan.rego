# Rules for an OpenTofu plan, read from the JSON that
# `tofu show -json <planfile>` prints.
package main

# Types whose objects hold data that a delete would lose. Add the project's
# own data stores.
protected_types := {
	"aws_db_instance",
	"aws_dynamodb_table",
	"aws_efs_file_system",
	"aws_kms_key",
	"aws_rds_cluster",
	"aws_s3_bucket",
}

# Tags every taggable resource must carry, set by the provider's
# default_tags or by the resource itself.
required_tags := {"environment", "owner"}

deny contains msg if {
	some resource in input.resource_changes
	resource.type in protected_types
	"delete" in resource.change.actions
	msg := sprintf("%s would be deleted or replaced, losing its data", [resource.address])
}

deny contains msg if {
	some resource in input.resource_changes
	some action in resource.change.actions
	action in {"create", "update"}
	taggable(resource.change)
	missing := required_tags - object.keys(planned_tags(resource.change))
	count(missing) > 0
	msg := sprintf("%s is missing the tags %v", [resource.address, sort(missing)])
}

# AWS resources that take tags have a tags_all attribute.
taggable(change) if "tags_all" in object.keys(change.after)

taggable(change) if change.after_unknown.tags_all

# tags_all is unknown until apply when no tags are set at all, so fall back
# to the resource's own tags.
planned_tags(change) := tags if {
	tags := change.after.tags_all
	is_object(tags)
} else := tags if {
	tags := change.after.tags
	is_object(tags)
} else := {}
