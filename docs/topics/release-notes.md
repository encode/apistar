# Release Notes

## Version 0.4

The Version 0.4 release is a significant re-working of the API Star codebase.
As part of this there are a number of features that have been removed and not
yet made their way back in to the project:

* The API Docs have not yet been re-introduced.
* The command routing has not yet been re-introduced.
* The `apistar` command line tool has not yet been re-introduced.
* The ORM components have been removed. We'll be pushing for this kind of functionality to be addressed as third-party packages instead.

However the overall state of the project is in a much better place than it
was in 0.3, and I'm confident that we've now got a great base to build on.

We've also gained a number of new features and improvements:

* ASGI compatible. You'll be able to use either `uvicorn` or `daphne` as servers for use with ASyncApp.
* OpenAPI is now the default schema representation.
* We now have an event hooks API.
* The dependency injection now has a much cleaner, simpler API and implementation.
* The type system now has a much cleaner, simpler API and implementation.

If you do need to continue working against the 0.3 version, you should refer
to [the older documentation on GitHub][0.3]. You should also make sure to serve any
async applications using uvicorn <= 0.0.15, which uses the pre-ASGI interface style.

[0.3]: https://github.com/encode/apistar/tree/0.3.9
