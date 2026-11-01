## 7. Power Automate build, action by action

Use an automated cloud flow named `Email - Customs Invoice Extraction`. This is Power Automate cloud, not a desktop UI automation flow. Connection permissions and licensing must be checked in the client's tenant; no specific license purchase was established in this chat.

1. Add Office 365 Outlook **When a new email arrives (V3)**. Set Folder=Inbox, Subject Filter=`DH-CE-INV`, Only with Attachments=Yes, Include Attachments=No, Importance=Any. Leave To/CC/From unrestricted only if that is the intended client routing policy. The demonstrated workflow does not search the email body. Microsoft's connector guidance supports retrieving attachment bytes later with Get Attachment V2 [R5].
2. Add **Apply to each**. Select the trigger's **Attachments** array. An array is the collection of attachments; one loop iteration handles one attachment.
3. Add a **Condition** inside the loop. In the left Expression tab paste the following. Compare “is equal to” the Expression `true` (Boolean, not a quoted string). Verify the actual attachment property names in trigger run output when migrating to a different trigger/connector.

```text
and(
  not(equals(item()?['IsInline'], true)),
  or(
    endsWith(toLower(coalesce(item()?['Name'], '')), '.pdf'),
    endsWith(toLower(coalesce(item()?['Name'], '')), '.png'),
    endsWith(toLower(coalesce(item()?['Name'], '')), '.jpg'),
    endsWith(toLower(coalesce(item()?['Name'], '')), '.jpeg')
  )
)
```

`item()` selects the current loop attachment. `?` permits a missing property. `coalesce` supplies an empty string when Name is null. `toLower` permits PDF/Pdf/pdf. `endsWith` filters file extensions. `not(equals(...,true))` excludes explicit inline attachments. This extension filter does not prove a file is an invoice and permits missing IsInline; those are limitations of the demonstrated condition. See expression reference [R6].

4. In **If yes**, add Office 365 Outlook **Get Attachment (V2)**. Message Id=trigger Message Id. Attachment Id=current loop attachment ID. Original Mailbox Address was blank for the tested connected mailbox; shared-mailbox behavior must be configured separately. Sensitivity options were not established as a requirement.
5. Add OneDrive for Business **Create file** within If yes. Folder Path=`/InvoiceIntake/Incoming`. File Content=**Content Bytes** from Get Attachment V2. Do not substitute the name or ID for file content. Leave If no empty to ignore unsupported attachments.
6. Filename reconstruction matching the observed GUID-prefix convention:

```text
concat(guid(), '_', item()?['Name'])
```

This exact expanded expression is a replication recommendation; the screenshot showed only `concat(...)`. GUID distinguishes filenames; the engine later deduplicates document contents using SHA-256. Filename character/path constraints remain applicable [R7]. Do not claim this expression sanitizes names or prevents duplicate processing across separate tenant instances.
7. Save. Use a controlled email with subject containing `DH-CE-INV` and a known invoice PDF. Verify flow run history: trigger, loop condition true, Get Attachment success, Create file success. Then verify the local file appears. The tested filename example is `6cb13c61-f60b-47dc-b338-ec9e8cccaa47_small invoice - 3 line items.PDF`.

```powershell
$incoming = Join-Path $env:OneDriveCommercial 'InvoiceIntake\Incoming'
Test-Path -LiteralPath $incoming
Get-ChildItem -LiteralPath $incoming -File |
    Select-Object Name, Length, LastWriteTime |
    Format-Table -AutoSize
```

Acceptance: file opens as the intended invoice; bytes/content are not an attachment ID or encoded-text document. Export the completed flow and capture connection references for the client's release record. A flow export is not included in the evidence supplied here.

