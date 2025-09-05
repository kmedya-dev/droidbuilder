import os
import unittest
import zipfile
import tarfile
from unittest.mock import patch, MagicMock
from droidbuilder.utils import _safe_join, _safe_extract_zip, _safe_extract_tar

class TestInstallerHelpers(unittest.TestCase):

    def test_safe_join(self):
        base = '/tmp'
        self.assertEqual(_safe_join(base, 'foo', 'bar'), '/tmp/foo/bar')
        with self.assertRaises(IOError):
            _safe_join(base, '../foo')

    @patch('droidbuilder.utils.logger')
    @patch('os.makedirs')
    @patch('builtins.open')
    @patch('shutil.copyfileobj')
    def test_safe_extract_zip(self, mock_copy, mock_open, mock_makedirs, mock_logger):
        zip_ref = MagicMock(spec=zipfile.ZipFile)
        zip_info = zipfile.ZipInfo('dir/file.txt')
        zip_ref.infolist.return_value = [
            zipfile.ZipInfo('dir/'),
            zip_info
        ]
        zip_ref.open.return_value.__enter__.return_value = MagicMock()

        _safe_extract_zip(zip_ref, '/tmp')

        mock_makedirs.assert_any_call('/tmp/dir', exist_ok=True)
        mock_open.assert_called_once_with('/tmp/dir/file.txt', 'wb')
        mock_copy.assert_called_once()

    @patch('droidbuilder.utils.logger')
    @patch('os.path.exists', return_value=False)
    @patch('os.chmod')
    @patch('os.makedirs')
    @patch('builtins.open')
    @patch('shutil.copyfileobj')
    def test_safe_extract_tar(self, mock_copy, mock_open, mock_makedirs, mock_chmod, mock_exists, mock_logger):
        tar_ref = MagicMock(spec=tarfile.TarFile)
        tar_member_dir = tarfile.TarInfo('dir/')
        tar_member_dir.type = tarfile.DIRTYPE
        tar_member_file = tarfile.TarInfo('dir/file.txt')
        tar_member_file.type = tarfile.REGTYPE
        tar_member_file.mode = 0o644
        tar_ref.getmembers.return_value = [tar_member_dir, tar_member_file]
        tar_ref.extractfile.return_value.__enter__.return_value = MagicMock()

        _safe_extract_tar(tar_ref, '/tmp')

        mock_makedirs.assert_any_call('/tmp/dir', exist_ok=True)
        mock_open.assert_called_once_with('/tmp/dir/file.txt', 'wb')
        mock_copy.assert_called_once()
        mock_chmod.assert_called_once_with('/tmp/dir/file.txt', 0o644)

if __name__ == '__main__':
    unittest.main()